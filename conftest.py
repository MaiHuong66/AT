import os
from urllib.parse import quote
import pytest
from selenium import webdriver
from helpers.flutter_helper import SCREENSHOT_DIR, FlutterHelper
from helpers.login import login, select_context
from locators import anomaly_report as L
BASE = "mesgo-bunbo.kaizengo.vn"
CONTEXT_WAIT = 2    # số giây chờ hộp thoại chọn nhà máy hiện lại sau mỗi lần tải trang
_SECRET_ENV = ("MESGO_USER", "MESGO_PASS", "MESGO_ACC_PASS")

def auth_url():
    u = quote(os.environ["MESGO_USER"], safe="")
    p = quote(os.environ["MESGO_PASS"], safe="")
    return f"https://{u}:{p}@{BASE}/"

def open_site(driver, path=""):
    driver.get(auth_url())                  # nạp thông tin Basic Auth
    driver.get(f"https://{BASE}/{path}")    # vào bằng URL sạch (Flutter không chạy được khi URL có user:pass)

def dump_failure(driver, name):
    """Chụp ảnh, in chữ đang hiện trên màn hình và log lỗi của trình duyệt (đã ẩn thông tin đăng nhập)."""
    secrets = []
    for key in _SECRET_ENV:
        value = os.environ.get(key, "")
        secrets += [value, quote(value, safe="")]

    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{name}.png"))
    except Exception:
        pass

    print(f"\n===== CHỮ ĐANG HIỆN TRÊN MÀN HÌNH ({name}) =====")
    try:
        texts = driver.execute_script("""
            return [...document.querySelectorAll('flt-semantics')]
              .filter(e => !e.querySelector('flt-semantics') && e.textContent.trim())
              .map(e => (e.getAttribute('role') || '-') + ' | ' + e.textContent.trim().replace(/\\s+/g, ' ').slice(0, 80));
        """)
        for t in texts:
            print("  ", t)
    except Exception as ex:
        print("  (không đọc được)", str(ex)[:100])

    print(f"===== LOG TRÌNH DUYỆT (cảnh báo/lỗi, {name}) =====")
    try:
        for e in driver.get_log("browser"):
            if e["level"] in ("SEVERE", "WARNING"):
                msg = e["message"]
                for s in secrets:
                    if s:
                        msg = msg.replace(s, "***")
                print(" ", e["level"], "|", msg[:300])
    except Exception as ex:
        print("  (không đọc được log)", str(ex)[:100])

@pytest.fixture(scope="session")
def driver():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    d = webdriver.Chrome(options=opts)
    d.maximize_window()
    yield d
    d.quit()

@pytest.fixture(scope="session")
def logged_in(driver):
    """Đăng nhập một lần cho cả phiên test."""
    open_site(driver)
    f = FlutterHelper(driver)
    f.enable_semantics()
    try:
        login(f)
    except Exception:
        dump_failure(driver, "loi_dang_nhap")
        raise
    return f

@pytest.fixture
def anomaly_page(driver, logged_in):
    """Mỗi test bắt đầu từ trang Phiếu báo cáo bất thường mới tải lại."""
    f = logged_in
    driver.get(f"https://{BASE}/anomaly-report")
    f.enable_semantics()
    try:
        select_context(f, timeout=CONTEXT_WAIT)   # nếu hộp thoại hiện lại thì xác nhận lại
        f.find(L.ALL_ROWS)
        f.wait_texts_settled(L.ALL_ROWS)           # chờ bảng tải xong và ngừng cập nhật
    except Exception:
        dump_failure(driver, "loi_trang_phieu")
        raise
    return f

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Khi test lỗi, đính ảnh chụp màn hình vào báo cáo HTML."""
    outcome = yield
    report = outcome.get_result()
    if report.when in ("setup", "call") and report.failed:
        d = item.funcargs.get("driver")
        if d is None:
            return
        try:
            from pytest_html import extras
            png = d.get_screenshot_as_base64()
            report.extras = getattr(report, "extras", []) + [extras.png(png, "Màn hình lúc lỗi")]
        except Exception:
            pass
