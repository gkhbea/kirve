"""
KİRVE AI OS - Ev Otomasyonu ve IoT Kontrol Aracı (ev_otomasyon)
Google Home APIs, Togg T10X ve Roborock Q8 cihaz entegrasyonu.
Ağ zaman aşımı (timeout) durumunda çökmeyen, loglayan ve arka planda
yeniden deneme (retry) döngüsü çalıştıran dayanıklı (resilient) mimari.
"""
import time
import json
import threading
import queue
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from kirve.memory import KirveMemory

# ----------------------------------------------------------------------
# 1. API İSTEK / YANIT ŞEMALARI (Data Schemas)
# ----------------------------------------------------------------------

@dataclass
class ToggChargeRequest:
    """Togg T10X şarj kontrol API istek şeması."""
    vin: str
    action: str = "START"                 # "START" veya "STOP"
    target_soc_percentage: int = 80       # Hedef şarj seviyesi (%0 - 100)
    charging_power_kw: float = 22.0       # kW AC/DC


@dataclass
class ToggClimateRequest:
    """Togg T10X iklimlendirme/klima API istek şeması."""
    vin: str
    action: str = "START"                 # "START" veya "STOP"
    target_temperature_c: float = 22.0
    defrost: bool = False


@dataclass
class ToggLockRequest:
    """Togg T10X kapı kilidi API istek şeması."""
    vin: str
    lock: bool = True


@dataclass
class ToggApiResponse:
    """Togg T10X standart API yanıt şeması."""
    success: bool
    device: str = "Togg T10X"
    telemetry: Optional[Dict[str, Any]] = None
    message: str = ""
    error: Optional[str] = None
    is_timeout: bool = False
    retry_task_id: Optional[str] = None


@dataclass
class ToggT10XStatus:
    """Togg T10X telemetri yanıt şeması."""
    vin: str
    battery_percentage: int      # 0 - 100
    range_km: int                # Kalan menzil
    is_charging: bool
    charging_power_kw: float     # kW şarj gücü (AC/DC)
    charge_remaining_minutes: int
    doors_locked: bool
    climate_active: bool
    target_temperature_c: float
    last_updated: float


@dataclass
class RoborockCleanRequest:
    """Roborock Q8 temizlik API istek şeması."""
    device_id: str
    command: str = "clean_zone"           # "clean_zone", "clean_all", "dock", "pause", "resume"
    zone_name: Optional[str] = None       # "Salon", "Mutfak", "Yatak Odası" vb.
    suction_power: str = "balanced"       # "quiet", "balanced", "turbo", "max"
    water_level: str = "medium"           # "off", "low", "medium", "high"
    clean_passes: int = 1


@dataclass
class RoborockApiResponse:
    """Roborock Q8 standart API yanıt şeması."""
    success: bool
    device: str = "Roborock Q8"
    telemetry: Optional[Dict[str, Any]] = None
    message: str = ""
    error: Optional[str] = None
    is_timeout: bool = False
    retry_task_id: Optional[str] = None


@dataclass
class RoborockQ8Status:
    """Roborock Q8 robot süpürge telemetri yanıt şeması."""
    device_id: str
    battery_percentage: int
    cleaning_state: str          # "docked", "cleaning", "paused", "returning", "error"
    lidar_status: str            # "OK", "DIRTY", "BLOCKED"
    mop_attached: bool
    water_level: str             # "high", "medium", "low"
    current_zone: Optional[str]
    cleaned_area_m2: float
    cleaning_time_minutes: int
    last_updated: float


@dataclass
class GoogleHomeDevice:
    """Google Home cihaz şeması."""
    device_id: str
    name: str
    type: str                    # "LIGHT", "THERMOSTAT", "SWITCH", "OUTLET"
    room: str
    is_online: bool
    state: Dict[str, Any]


@dataclass
class GoogleHomeCommandRequest:
    """Google Home standard trait komut istek şeması."""
    device_id: str
    command: str                          # örn: "action.devices.commands.OnOff", "set_brightness"
    params: Optional[Dict[str, Any]] = None


@dataclass
class GoogleHomeCommandResponse:
    """Google Home standard trait komut yanıt şeması."""
    success: bool
    device_id: str
    device_name: str = ""
    command: str = ""
    current_state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ----------------------------------------------------------------------
# 2. DAYANIKLI ARKA PLAN RETRY (YENİDEN DENEME) DÖNGÜSÜ
# ----------------------------------------------------------------------

@dataclass
class RetryTask:
    task_id: str
    device_name: str
    action_fn: Callable[[], Any]
    callback: Optional[Callable[[Any], None]]
    max_retries: int
    current_retry: int
    delay_seconds: float
    last_error: str
    created_at: float

class DeviceRetryWorker:
    """
    Arka planda çalışan, zaman aşımına uğrayan cihaz isteklerini
    sistemi tıkamadan ve çökertmeden belirli aralıklarla yeniden deneyen işçi (worker).
    """
    def __init__(self, memory: Optional[KirveMemory] = None, interval: float = 2.0):
        self.memory = memory or KirveMemory()
        self.interval = interval
        self.queue: List[RetryTask] = []
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True, name="KirveRetryWorker")
        self._worker_thread.start()

    def add_retry_task(self, device_name: str, action_fn: Callable[[], Any],
                       callback: Optional[Callable[[Any], None]] = None,
                       max_retries: int = 3, delay_seconds: float = 2.0,
                       initial_error: str = "Timeout") -> str:
        task_id = f"retry_{device_name}_{int(time.time() * 1000)}"
        task = RetryTask(
            task_id=task_id,
            device_name=device_name,
            action_fn=action_fn,
            callback=callback,
            max_retries=max_retries,
            current_retry=0,
            delay_seconds=delay_seconds,
            last_error=initial_error,
            created_at=time.time()
        )
        with self._lock:
            self.queue.append(task)
        
        self.memory.log_event("WARNING", f"[{device_name}] Bağlantı zaman aşımı. Yeniden deneme kuyruğuna alındı (ID: {task_id}). Hata: {initial_error}")
        return task_id

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self.interval)
            with self._lock:
                if not self.queue:
                    continue
                tasks_to_process = list(self.queue)

            for task in tasks_to_process:
                task.current_retry += 1
                try:
                    result = task.action_fn()
                    # Başarılı olduysa kuyruktan çıkar
                    with self._lock:
                        if task in self.queue:
                            self.queue.remove(task)
                    self.memory.log_event("INFO", f"[{task.device_name}] Yeniden deneme başarılı oldu (Deneme {task.current_retry}/{task.max_retries}).")
                    if task.callback:
                        task.callback(result)
                except Exception as e:
                    task.last_error = str(e)
                    if task.current_retry >= task.max_retries:
                        with self._lock:
                            if task in self.queue:
                                self.queue.remove(task)
                        self.memory.log_event("ERROR", f"[{task.device_name}] Maksimum yeniden deneme ({task.max_retries}) aşıldı. İstek başarısız oldu: {str(e)}")

    def get_queue_status(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [{
                "task_id": t.task_id,
                "device_name": t.device_name,
                "current_retry": t.current_retry,
                "max_retries": t.max_retries,
                "last_error": t.last_error
            } for t in self.queue]

    def stop(self) -> None:
        self._stop_event.set()

# ----------------------------------------------------------------------
# 3. GOOGLE HOME APIs İSTEMCİSİ
# ----------------------------------------------------------------------

class GoogleHomeClient:
    """
    Google Smart Home APIs simülatör ve entegrasyon katmanı.
    """
    def __init__(self, simulate_network: bool = True):
        self.simulate_network = simulate_network
        self.devices: Dict[str, GoogleHomeDevice] = {
            "light_salon": GoogleHomeDevice(
                device_id="light_salon",
                name="Salon Avizesi",
                type="LIGHT",
                room="Salon",
                is_online=True,
                state={"on": True, "brightness": 80, "color_temp_k": 3000}
            ),
            "thermostat_ev": GoogleHomeDevice(
                device_id="thermostat_ev",
                name="Ev Termostatı",
                type="THERMOSTAT",
                room="Koridor",
                is_online=True,
                state={"temperature_c": 22.5, "target_temperature_c": 23.0, "mode": "heat"}
            ),
            "plug_kahve": GoogleHomeDevice(
                device_id="plug_kahve",
                name="Kahve Makinesi Prizi",
                type="OUTLET",
                room="Mutfak",
                is_online=True,
                state={"on": False}
            )
        }

    def list_devices(self) -> List[Dict[str, Any]]:
        return [asdict(d) for d in self.devices.values()]

    def execute_command(self, device_id: str, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        device = self.devices.get(device_id)
        if not device:
            raise KeyError(f"Google Home cihazı bulunamadı: {device_id}")

        if not device.is_online:
            raise TimeoutError(f"Cihaza ulaşılamıyor (Google Home Gateway timeout): {device.name}")

        params = params or {}
        if command in ["action.devices.commands.OnOff", "turn_on"]:
            device.state["on"] = True
        elif command in ["action.devices.commands.OnOff_off", "turn_off"]:
            device.state["on"] = False
        elif command == "set_brightness":
            device.state["brightness"] = params.get("brightness", device.state.get("brightness", 100))
        elif command == "set_temperature":
            device.state["target_temperature_c"] = params.get("target_temperature", 22.0)

        return {
            "success": True,
            "device_id": device_id,
            "device_name": device.name,
            "command": command,
            "current_state": device.state
        }

# ----------------------------------------------------------------------
# 4. EV OTOMASYON ARACI (EvOtomasyonAraci)
# ----------------------------------------------------------------------

class EvOtomasyonAraci:
    """
    KİRVE AI OS Ana Ev ve Cihaz Otomasyon Aracı.
    Togg T10X, Roborock Q8 ve Google Home cihazlarını yönetir.
    Ağ hatalarında sistemi kilitlemez, arka planda yeniden deneme mekanizmasını devreye sokar.
    """
    def __init__(self, memory: Optional[KirveMemory] = None):
        self.memory = memory or KirveMemory()
        self.retry_worker = DeviceRetryWorker(memory=self.memory)
        self.google_home = GoogleHomeClient()
        
        # Cihaz sanal telemetri durumları
        self._togg_status = ToggT10XStatus(
            vin="TR-TOGG-T10X-2024-V2",
            battery_percentage=78,
            range_km=395,
            is_charging=False,
            charging_power_kw=0.0,
            charge_remaining_minutes=0,
            doors_locked=True,
            climate_active=False,
            target_temperature_c=22.0,
            last_updated=time.time()
        )

        self._roborock_status = RoborockQ8Status(
            device_id="RR-Q8-MAX-LIDAR-01",
            battery_percentage=94,
            cleaning_state="docked",
            lidar_status="OK",
            mop_attached=True,
            water_level="medium",
            current_zone=None,
            cleaned_area_m2=42.5,
            cleaning_time_minutes=38,
            last_updated=time.time()
        )

        # Ağ simülasyon bayrakları (testlerde timeout üretmek için kullanılabilir)
        self.simulate_togg_timeout = False
        self.simulate_roborock_timeout = False

    # --- TOGG T10X METOTLARI ---

    def get_togg_status(self) -> Dict[str, Any]:
        """
        Togg T10X batarya, menzil ve kilit durumunu sorgular.
        Timeout oluşursa sistemi çökertmez, loglar ve fallback döner.
        """
        def _fetch():
            if self.simulate_togg_timeout:
                raise TimeoutError("Togg T10X telematik sunucusuna ulaşılamadı (zaman aşımı).")
            self._togg_status.last_updated = time.time()
            return asdict(self._togg_status)

        try:
            data = _fetch()
            return {"success": True, "device": "Togg T10X", "telemetry": data}
        except TimeoutError as e:
            # Arka plan deneme kuyruğuna ekle
            task_id = self.retry_worker.add_retry_task(
                device_name="Togg T10X",
                action_fn=_fetch,
                initial_error=str(e)
            )
            return {
                "success": False,
                "device": "Togg T10X",
                "error": str(e),
                "is_timeout": True,
                "retry_task_id": task_id,
                "cached_telemetry": asdict(self._togg_status),
                "message": "Togg T10X ile iletişimde zaman aşımı yaşandı patron. Durum loglandı ve arka planda yeniden deneniyor."
            }

    def set_togg_charging(self, start: bool) -> Dict[str, Any]:
        """Togg şarjını başlatır veya durdurur."""
        if self.simulate_togg_timeout:
            return self.get_togg_status()

        self._togg_status.is_charging = start
        self._togg_status.charging_power_kw = 22.0 if start else 0.0
        self._togg_status.charge_remaining_minutes = 45 if start else 0
        action_desc = "başlatıldı" if start else "durduruldu"
        return {
            "success": True,
            "message": f"Togg T10X şarjı {action_desc} patron (Güç: {self._togg_status.charging_power_kw} kW).",
            "telemetry": asdict(self._togg_status)
        }

    def send_togg_charge_request(self, req: ToggChargeRequest) -> ToggApiResponse:
        """ToggChargeRequest şeması ile şarj kontrolü yapar."""
        is_start = req.action.upper() == "START"
        res = self.set_togg_charging(is_start)
        return ToggApiResponse(
            success=res.get("success", False),
            device="Togg T10X",
            telemetry=res.get("telemetry"),
            message=res.get("message", ""),
            error=res.get("error"),
            is_timeout=res.get("is_timeout", False),
            retry_task_id=res.get("retry_task_id")
        )

    def send_togg_climate_request(self, req: ToggClimateRequest) -> ToggApiResponse:
        """ToggClimateRequest şeması ile iklimlendirme kontrolü yapar."""
        if self.simulate_togg_timeout:
            res = self.get_togg_status()
            return ToggApiResponse(
                success=False,
                device="Togg T10X",
                error=res.get("error"),
                is_timeout=True,
                retry_task_id=res.get("retry_task_id"),
                message=res.get("message", "")
            )
        is_start = req.action.upper() == "START"
        self._togg_status.climate_active = is_start
        self._togg_status.target_temperature_c = req.target_temperature_c
        msg = f"Togg T10X kliması {req.target_temperature_c}°C ayarına {'başlatıldı' if is_start else 'durduruldu'} patron."
        return ToggApiResponse(
            success=True,
            device="Togg T10X",
            telemetry=asdict(self._togg_status),
            message=msg
        )

    def send_togg_lock_request(self, req: ToggLockRequest) -> ToggApiResponse:
        """ToggLockRequest şeması ile kapı kilidi kontrolü yapar."""
        if self.simulate_togg_timeout:
            res = self.get_togg_status()
            return ToggApiResponse(
                success=False,
                device="Togg T10X",
                error=res.get("error"),
                is_timeout=True,
                retry_task_id=res.get("retry_task_id"),
                message=res.get("message", "")
            )
        self._togg_status.doors_locked = req.lock
        msg = f"Togg T10X kapıları {'kilitlendi' if req.lock else 'açıldı'} patron."
        return ToggApiResponse(
            success=True,
            device="Togg T10X",
            telemetry=asdict(self._togg_status),
            message=msg
        )

    # --- ROBOROCK Q8 METOTLARI ---

    def get_roborock_status(self) -> Dict[str, Any]:
        """
        Roborock Q8 LiDAR, batarya ve temizlik durumunu sorgular.
        """
        def _fetch():
            if self.simulate_roborock_timeout:
                raise TimeoutError("Roborock Q8 yerel IP/Cloud bağlantısı zaman aşımına uğradı.")
            self._roborock_status.last_updated = time.time()
            return asdict(self._roborock_status)

        try:
            data = _fetch()
            return {"success": True, "device": "Roborock Q8", "telemetry": data}
        except TimeoutError as e:
            task_id = self.retry_worker.add_retry_task(
                device_name="Roborock Q8",
                action_fn=_fetch,
                initial_error=str(e)
            )
            return {
                "success": False,
                "device": "Roborock Q8",
                "error": str(e),
                "is_timeout": True,
                "retry_task_id": task_id,
                "cached_telemetry": asdict(self._roborock_status),
                "message": "Roborock Q8'e şu an ulaşılamıyor patron. LiDAR durumu son kayıttan korundu, arka planda yeniden deneniyor."
            }

    def send_roborock_clean_request(self, req: RoborockCleanRequest) -> RoborockApiResponse:
        """RoborockCleanRequest şeması ile temizlik komutunu icra eder."""
        if req.command in ["dock", "return_to_dock"]:
            res = self.dock_roborock()
        else:
            if req.water_level:
                self._roborock_status.water_level = req.water_level
            zone = req.zone_name or "Tüm Ev"
            res = self.start_zone_cleaning(zone)

        return RoborockApiResponse(
            success=res.get("success", False),
            device="Roborock Q8",
            telemetry=asdict(self._roborock_status),
            message=res.get("message", ""),
            error=res.get("error"),
            is_timeout=res.get("is_timeout", False),
            retry_task_id=res.get("retry_task_id")
        )

    def start_zone_cleaning(self, zone_name: str) -> Dict[str, Any]:
        """
        Roborock Q8'i belirli bir bölgeyi (salon, mutfak, çalışma odası vb.) temizlemesi için başlatır.
        """
        if self.simulate_roborock_timeout:
            return self.get_roborock_status()

        if self._roborock_status.lidar_status != "OK":
            return {
                "success": False,
                "error": f"LiDAR sensörü engelli ({self._roborock_status.lidar_status}). Temizlik başlatılamaz.",
                "message": "Patron, Roborock LiDAR sensörü kirli veya engelli görünüyor. Önce sensörü kontrol etmelisin."
            }

        self._roborock_status.cleaning_state = "cleaning"
        self._roborock_status.current_zone = zone_name
        return {
            "success": True,
            "device": "Roborock Q8",
            "message": f"Roborock Q8 '{zone_name}' bölgesinde temizliğe başladı patron (LiDAR aktif).",
            "telemetry": asdict(self._roborock_status)
        }

    def dock_roborock(self) -> Dict[str, Any]:
        """Roborock'ı şarj istasyonuna döndürür."""
        self._roborock_status.cleaning_state = "docked"
        self._roborock_status.current_zone = None
        return {
            "success": True,
            "message": "Roborock Q8 şarj istasyonuna döndü patron.",
            "telemetry": asdict(self._roborock_status)
        }

    # --- GOOGLE HOME KONTROLLERİ ---

    def execute_google_home_command(self, req: GoogleHomeCommandRequest) -> GoogleHomeCommandResponse:
        """GoogleHomeCommandRequest şeması ile Google Home komutu çalıştırır."""
        res = self.control_home_device(req.device_id, req.command, req.params)
        return GoogleHomeCommandResponse(
            success=res.get("success", False),
            device_id=req.device_id,
            device_name=res.get("device_name", ""),
            command=req.command,
            current_state=res.get("current_state"),
            error=res.get("error")
        )

    def control_home_device(self, device_id: str, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Google Home cihazına komut gönderir."""
        try:
            return self.google_home.execute_command(device_id, command, params)
        except Exception as e:
            self.memory.log_event("WARNING", f"[Google Home] {device_id} cihaz komutu hatası: {str(e)}")
            return {
                "success": False,
                "device_id": device_id,
                "error": str(e),
                "message": f"Google Home cihazı kontrol edilemedi: {str(e)}"
            }

    def list_home_devices(self) -> List[Dict[str, Any]]:
        return self.google_home.list_devices()

    def get_retry_status(self) -> List[Dict[str, Any]]:
        return self.retry_worker.get_queue_status()

    def close(self):
        self.retry_worker.stop()
