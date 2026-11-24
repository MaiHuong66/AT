import os

from helpers.waits import wait_until
from locators import login as LG


def _open_user_dropdown(f, attempts=3):
    """Mở dropdown Người dùng; thử lại nếu ô Search chưa hiện."""
    for i in range(attempts):
        f.click_real(LG.USER_DROPDOWN)
        if wait_until(lambda: f.driver.find_elements(*LG.SEARCH_INPUT), 5, step=0.2):
            return
        f.shot(f"login_loi_mo_dropdown_lan_{i + 1}")
    raise AssertionError(
        "Không mở được dropdown Người dùng sau 3 lần thử (xem reports/screenshots/login_loi_mo_dropdown_*.png)")


def _choose(f, dropdown, value):
    """Mở một dropdown trong hộp thoại và chọn lựa chọn có chữ đúng bằng `value`."""
    f.click_real(dropdown)
    f.click_real(LG.option_any(value))
    f.wait_gone(LG.SEARCH_INPUT, 5)      # chờ danh sách đóng lại (nếu dropdown có ô Search)


def select_context(f, timeout=6):
    """Nếu hộp thoại chọn nhà máy / loại sản phẩm đang hiện thì chọn và xác nhận.
    Trả về True nếu đã xử lý, False nếu hộp thoại không hiện trong `timeout` giây."""
    if not wait_until(lambda: f.driver.find_elements(*LG.CONTEXT_CONFIRM), timeout, step=0.2):
        return False

    _choose(f, LG.FACTORY_DROPDOWN, os.environ["MESGO_FACTORY"])
    _choose(f, LG.PRODUCT_DROPDOWN, os.environ["MESGO_PRODUCT"])

    f.click_real(LG.CONTEXT_CONFIRM)
    f.wait.until(lambda d: not d.find_elements(*LG.CONTEXT_CONFIRM))
    return True


def login(f):
    name = os.environ["MESGO_ACC_NAME"]
    pwd = os.environ["MESGO_ACC_PASS"]

    # 1. Chờ màn hình đăng nhập dựng xong rồi chọn người dùng trong dropdown
    f.find(LG.LOGIN_BUTTON)
    _open_user_dropdown(f)
    f.click_real(LG.SEARCH_INPUT)        # click vào ô Search để nó được focus
    f.wait_input_focused()
    f.type_into_focused(name)
    f.click_real(LG.user_option(name), hold=0.6)   # chờ danh sách lọc xong và đứng yên rồi mới click
    f.wait_gone(LG.SEARCH_INPUT, 5)

    # 2. Nhập mật khẩu và đăng nhập
    f.type(LG.PASSWORD, pwd)
    f.click_real(LG.LOGIN_BUTTON)
    f.wait.until(lambda d: not d.find_elements(*LG.LOGIN_BUTTON))

    # 3. Hộp thoại chọn nhà máy / loại sản phẩm
    select_context(f, timeout=10)
