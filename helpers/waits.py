import time

def wait_until(predicate, timeout=10, step=0.3, stable=0.0):
    """Chờ đến khi predicate() trả về giá trị đúng.

    - timeout: số giây chờ tối đa.
    - step:    khoảng cách giữa hai lần kiểm tra.
    - stable:  nếu > 0, điều kiện phải đúng LIÊN TỤC ít nhất từng đó giây
               (dùng khi giao diện Flutter còn đang cập nhật dở).

    Trả về True nếu điều kiện đạt, False nếu hết thời gian. Lỗi phát sinh trong
    predicate (stale element, chưa có phần tử...) được coi là "chưa đạt".
    """
    end = time.monotonic() + timeout
    ok_since = None
    while True:
        try:
            ok = bool(predicate())
        except Exception:
            ok = False
        now = time.monotonic()
        if ok:
            if ok_since is None:
                ok_since = now
            if now - ok_since >= stable:
                return True
        else:
            ok_since = None
        if now >= end:
            return False
        time.sleep(step)
