from app.security import hash_password, validate_upload, verify_password

PDF = b"%PDF-1.4\n" + b"0" * 100


def test_valid_pdf_accepted():
    r = validate_upload("invoice.pdf", PDF)
    assert r.ok and r.ext == "pdf" and len(r.sha256) == 64


def test_wrong_extension_rejected():
    assert not validate_upload("invoice.exe", PDF).ok


def test_renamed_file_rejected():
    assert not validate_upload("invoice.pdf", b"MZ\x90\x00 not really a pdf").ok


def test_oversize_rejected():
    assert not validate_upload("big.pdf", b"%PDF-" + b"0" * (11 * 1024 * 1024)).ok


def test_pdf_with_javascript_rejected():
    assert not validate_upload("x.pdf", PDF + b"/JavaScript (app.alert(1))").ok


def test_filename_sanitised():
    r = validate_upload("../../etc/pass<wd>.pdf", PDF)
    assert r.ok and "/" not in r.safe_name and "<" not in r.safe_name


def test_password_hash_roundtrip():
    h = hash_password("correct horse battery")
    assert h.startswith("pbkdf2_sha256$")
    assert verify_password("correct horse battery", h)
    assert not verify_password("wrong", h)
    assert hash_password("same") != hash_password("same")   # random salt
