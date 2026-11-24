import re

import pytest
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from helpers.waits import wait_until
from locators import anomaly_report as L

STATUS_PATTERN = re.compile(r"^\d+ BT\d+ (Đang xử lý|Hoàn thành)")


# ---------- Hàm hỗ trợ ----------
def rows(f):
    """Chữ của các dòng đang hiện trong bảng, đọc trong một lệnh (tránh stale element)."""
    return f.texts(L.ALL_ROWS)


def status_of(row):
    """Dòng có dạng 'STT MÃ TRẠNG_THÁI ...' → trả về trạng thái ngay sau mã phiếu."""
    m = STATUS_PATTERN.match(row)
    return m.group(1) if m else None


def only_status(rs, status):
    return bool(rs) and all(status_of(r) == status for r in rs)


def has_mixed_status(rs):
    return len({status_of(r) for r in rs}) >= 2


def reset(f):
    """Xoá bộ lọc (app nhớ bộ lọc giữa các lần tải lại) và chờ bảng về đủ các trạng thái."""
    f.click_real(L.CLEAR_FILTER)
    assert wait_until(lambda: has_mixed_status(rows(f)), 12), \
        f"Bảng chưa về trạng thái ban đầu: {rows(f)[:3]}"
    f.wait_texts_settled(L.ALL_ROWS)         # chờ việc xoá bộ lọc tải lại xong, tránh xoá mất chữ vừa gõ


def search(f, text, found=True):
    """Gõ vào ô tìm kiếm rồi chờ kết quả ổn định 1 giây.

    found=True : chờ bảng có ít nhất 1 dòng và MỌI dòng đều chứa `text`
                 (bảng rỗng là trạng thái đang tải nên KHÔNG được tính là xong).
    found=False: chờ bảng rỗng.
    """
    if found:
        done = lambda: (lambda rs: bool(rs) and all(text in r for r in rs))(rows(f))
    else:
        done = lambda: rows(f) == []
    for _ in range(3):                       # chữ gõ có thể bị mất: gõ lại (xoá sạch trước) nếu bảng chưa lọc
        f.click_real(L.SEARCH_INPUT)
        f.wait_input_focused()
        f.type_into_focused(text, clear=True)
        if wait_until(done, 8, stable=1.0):
            return


def filter_status(f, status):
    """Chọn một trạng thái trong dropdown và chờ bảng chỉ còn đúng trạng thái đó."""
    option = L.status_option(status)
    for _ in range(2):                      # mở dropdown; nếu lựa chọn chưa hiện thì đóng lại và mở lần nữa
        f.click_real(L.STATUS_FILTER)
        if wait_until(lambda: f.driver.find_elements(*option), 5, step=0.2):
            break
        ActionChains(f.driver).send_keys(Keys.ESCAPE).perform()
    f.click_real(option)
    applied = lambda: only_status(rows(f), status)
    if not wait_until(applied, 8, stable=0.5):
        ActionChains(f.driver).send_keys(Keys.ESCAPE).perform()   # có thể bộ lọc áp dụng khi đóng dropdown
        wait_until(applied, 8, stable=0.5)


# ---------- Test case ----------
def test_search_existing_code(anomaly_page):
    f = anomaly_page
    reset(f)
    search(f, "BT2611006")
    result = rows(f)
    assert len(result) == 1, f"Kết quả: {result}"
    assert "BT2611006" in result[0]


def test_search_not_existing_code(anomaly_page):
    f = anomaly_page
    reset(f)
    search(f, "BT0000000", found=False)
    assert rows(f) == []


@pytest.mark.parametrize("status", ["Đang xử lý", "Hoàn thành"])
def test_filter_by_status(anomaly_page, status):
    f = anomaly_page
    reset(f)
    filter_status(f, status)
    result = rows(f)
    assert result, f"Không có dòng nào khi lọc '{status}'"
    wrong = [r for r in result if status_of(r) != status]
    assert not wrong, f"Có dòng sai trạng thái (mong đợi '{status}'): {wrong[:3]}"


def test_filter_status_and_search(anomaly_page):
    f = anomaly_page
    reset(f)
    filter_status(f, "Hoàn thành")
    search(f, "BT2611005")
    result = rows(f)
    assert len(result) == 1, f"Kết quả: {result}"
    assert "BT2611005" in result[0] and status_of(result[0]) == "Hoàn thành"


def test_clear_filter_restores_all_statuses(anomaly_page):
    f = anomaly_page
    reset(f)
    filter_status(f, "Hoàn thành")
    assert only_status(rows(f), "Hoàn thành")
    f.click_real(L.CLEAR_FILTER)
    assert wait_until(lambda: has_mixed_status(rows(f)), 12), \
        f"Bảng chưa trở lại đủ trạng thái: {rows(f)[:3]}"
