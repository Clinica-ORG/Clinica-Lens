import uuid
import processing


def test_file_sha256_same_bytes_same_hash(tmp_path):
    a = tmp_path / "a.pdf"
    b = tmp_path / "sub_b.pdf"
    a.write_bytes(b"%PDF-1.4 hello")
    b.write_bytes(b"%PDF-1.4 hello")

    assert processing.file_sha256(str(a)) == processing.file_sha256(str(b))


def test_file_sha256_different_content_different_hash(tmp_path):
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    a.write_bytes(b"one")
    b.write_bytes(b"two")

    assert processing.file_sha256(str(a)) != processing.file_sha256(str(b))


def test_file_sha256_accepts_bytes():
    assert processing.file_sha256(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_point_id_is_deterministic_valid_uuid():
    pid = processing.point_id("doc123", 0)

    assert pid == processing.point_id("doc123", 0)
    uuid.UUID(pid)
