from selenium.webdriver.common.by import By

X = By.XPATH

STATUSES = ["Đang xử lý", "Hoàn thành", "Đã huỷ"]   # các trạng thái trong dropdown Trạng thái

# Dropdown Trạng thái: chữ là "Trạng thái" khi chưa chọn, đổi thành giá trị khi đã chọn
_STATUS_TEXTS = " or ".join(f"normalize-space(.)='{t}'" for t in ["Trạng thái"] + STATUSES)
STATUS_FILTER = (X, f"//flt-semantics[@role='button' and ({_STATUS_TEXTS})]")

SEARCH_INPUT  = (X, "//flt-semantics[.//input][not(.//flt-semantics)]")
CLEAR_FILTER  = (X, "//flt-semantics[@role='button' and contains(normalize-space(.),'Xoá bộ lọc')]")
CREATE_TICKET = (X, "//flt-semantics[@role='button' and normalize-space(.)='Tạo phiếu']")
REFRESH       = (X, "//flt-semantics[@role='button' and contains(normalize-space(.),'Làm mới')]")
ALL_ROWS      = (X, "//flt-semantics[@role='button' and contains(normalize-space(.),'BT26')]")


def status_option(name):
    """Lựa chọn trong dropdown Trạng thái: thẻ nhỏ nhất có chữ đúng bằng tên, không đòi hỏi role.
    Lấy thẻ xuất hiện cuối (danh sách mở ra sau cùng); dòng bảng có chữ dài hơn nên không khớp."""
    return (X, f"(//flt-semantics[not(.//flt-semantics) and normalize-space(.)='{name}'])[last()]")


def row_by_code(code):
    return (X, f"//flt-semantics[@role='button' and contains(normalize-space(.),'{code}')]")