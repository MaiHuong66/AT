import os

from selenium.common.exceptions import (
    MoveTargetOutOfBoundsException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers.waits import wait_until

SCREENSHOT_DIR = os.path.join("reports", "screenshots")

# Đọc chữ của nhiều phần tử trong MỘT lệnh để tránh stale element khi Flutter dựng lại cây thẻ.
_TEXTS_JS = """
const res = document.evaluate(arguments[0], document, null,
                              XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
const out = [];
for (let i = 0; i < res.snapshotLength; i++) {
    out.push(res.snapshotItem(i).textContent.trim().replace(/\\s+/g, ' '));
}
return out;
"""

_INPUT_FOCUSED_JS = "return ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)"
_ACTIVE_VALUE_JS = "const a = document.activeElement; return (a && a.value !== undefined) ? a.value : null"


class FlutterHelper:
    """Các thao tác chung cho web Flutter (đọc qua cây flt-semantics)."""

    def __init__(self, driver, timeout=20):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    # ---------- Khởi động ----------
    def enable_semantics(self):
        d = self.driver
        self.wait.until(lambda x: x.find_elements(By.CSS_SELECTOR, "flutter-view"))
        if d.find_elements(By.CSS_SELECTOR, "flt-semantics"):
            return
        d.execute_script("document.querySelector('flt-semantics-placeholder')?.click()")
        self.wait.until(lambda x: x.find_elements(By.CSS_SELECTOR, "flt-semantics"))

    # ---------- Tìm và chờ ----------
    def find(self, locator):
        try:
            return self.wait.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            raise TimeoutException(
                f"Không tìm thấy phần tử: {locator[1]}\n"
                f"Các thẻ có chữ đang hiện: {self.visible_texts()}") from None

    def visible_texts(self, limit=40):
        """Vài thẻ nhỏ nhất đang có chữ (role | chữ), dùng để chẩn đoán khi không tìm thấy phần tử."""
        try:
            items = self.driver.execute_script("""
                return [...document.querySelectorAll('flt-semantics')]
                  .filter(e => !e.querySelector('flt-semantics') && e.textContent.trim())
                  .map(e => (e.getAttribute('role') || '-') + ' | ' + e.textContent.trim().replace(/\\s+/g, ' ').slice(0, 40));
            """)
            return items[:limit]
        except Exception as ex:
            return f"(không đọc được: {str(ex)[:60]})"

    def wait_gone(self, locator, timeout=5):
        """Chờ phần tử biến mất (best effort, trả về True/False)."""
        return wait_until(lambda: not self.driver.find_elements(*locator), timeout, step=0.15)

    def wait_stable(self, locator, timeout=3, hold=0.3):
        """Chờ vị trí/kích thước phần tử đứng yên liên tục `hold` giây (Flutter đang dựng lại layout)."""
        last = [None]

        def same():
            try:
                r = self.driver.find_element(*locator).rect
            except Exception:
                last[0] = None
                return False
            cur = (r["x"], r["y"], r["width"], r["height"])
            ok = cur == last[0]
            last[0] = cur
            return ok

        return wait_until(same, timeout, step=0.15, stable=hold)

    def wait_input_focused(self, timeout=3):
        """Chờ Flutter tạo và focus ô nhập thật (best effort, trả về True/False)."""
        return wait_until(lambda: self.driver.execute_script(_INPUT_FOCUSED_JS), timeout, step=0.1)

    # ---------- Thao tác ----------
    def click_real(self, locator, retries=3, hold=0.3):
        """Chờ phần tử xuất hiện và đứng yên `hold` giây rồi click chuột thật vào giữa nó."""
        self.find(locator)
        self.wait_stable(locator, hold=hold)
        for attempt in range(retries):
            try:
                el = self.driver.find_element(*locator)   # lấy lại để tránh stale
                ActionChains(self.driver).move_to_element(el).click().perform()
                return
            except (StaleElementReferenceException, MoveTargetOutOfBoundsException, NoSuchElementException):
                if attempt == retries - 1:
                    raise
                wait_until(lambda: self.driver.find_elements(*locator), 5, step=0.15)

    def type_into_focused(self, value, clear=False, retries=3):
        """Gõ vào ô đang được focus và KIỂM TRA chữ đã vào ô (Flutter có lúc bỏ mất phím
        nếu gõ ngay sau khi click). Chưa vào thì xoá sạch và gõ lại, tối đa `retries` lần."""
        for _ in range(retries):
            chain = ActionChains(self.driver)
            if clear:
                chain.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(Keys.DELETE)
            chain.send_keys(value).perform()
            if wait_until(lambda: self.driver.execute_script(_ACTIVE_VALUE_JS) == value, 2, step=0.1):
                return True
            clear = True                    # lần sau xoá sạch rồi gõ lại
        return False

    def type(self, locator, value):
        """Click vào ô để Flutter tạo ô nhập thật rồi xoá chữ cũ và gõ chữ mới."""
        self.click_real(locator)
        self.wait_input_focused()
        self.type_into_focused(value, clear=True)

    # ---------- Đọc dữ liệu ----------
    def texts(self, locator):
        """Danh sách chữ của mọi phần tử khớp XPath, đọc trong một lệnh duy nhất."""
        if locator[0] != By.XPATH:
            raise ValueError("texts() chỉ hỗ trợ locator XPath")
        return self.driver.execute_script(_TEXTS_JS, locator[1])

    def wait_texts_settled(self, locator, timeout=15, stable=1.0):
        """Chờ danh sách chữ (ví dụ các dòng bảng) có dữ liệu và KHÔNG đổi liên tục `stable` giây,
        tức là trang đã tải xong và không còn cập nhật ngầm."""
        prev = [None]

        def settled():
            cur = self.texts(locator)
            ok = bool(cur) and cur == prev[0]
            prev[0] = cur
            return ok

        return wait_until(settled, timeout, step=0.3, stable=stable)

    def text(self, locator):
        return self.find(locator).get_attribute("textContent").strip()

    # ---------- Tiện ích ----------
    def shot(self, name):
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        self.driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{name}.png"))
