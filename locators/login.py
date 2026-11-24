from selenium.webdriver.common.by import By

X = By.XPATH
# --- Màn hình đăng nhập ---
USER_DROPDOWN = (X, "//flt-semantics[@role='button' and contains(normalize-space(.),'Người dùng')]")
SEARCH_INPUT = (X, "//flt-semantics[.//input][not(.//flt-semantics)]")
PASSWORD = (X, "//flt-semantics[not(@role) and not(normalize-space(.)) "
               "and count(./flt-semantics)=1 and ./flt-semantics[@role='button']]")
SHOW_PASS = (X, "//flt-semantics[not(@role) and not(normalize-space(.)) "
                "and count(./flt-semantics)=1]/flt-semantics[@role='button']")
LOGIN_BUTTON = (X, "//flt-semantics[@role='button' and contains(normalize-space(.),'Login')]")

# --- Hộp thoại chọn nhà máy / loại sản phẩm (hiện sau khi đăng nhập) ---
FACTORY_DROPDOWN = (X, "//flt-semantics[@role='button' and contains(normalize-space(.),'Chọn nhà máy')]")
PRODUCT_DROPDOWN = (X, "//flt-semantics[@role='button' and contains(normalize-space(.),'Loại sản phẩm')]")
CONTEXT_CONFIRM = (X, "//flt-semantics[@role='button' and normalize-space(.)='Xác nhận']")

def user_option(name):
    """Một người dùng trong danh sách đăng nhập."""
    return (X, f"//flt-semantics[@role='button' and normalize-space(.)='{name}']")

def option_any(name):
    """Lựa chọn trong dropdown: thẻ nhỏ nhất có chữ đúng bằng tên; lấy cái xuất hiện cuối (danh sách mở ra sau cùng)."""
    return (X, f"(//flt-semantics[not(.//flt-semantics) and normalize-space(.)='{name}'])[last()]")