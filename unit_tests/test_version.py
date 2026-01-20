import pytest
from fastapi.testclient import TestClient
from main_app.main import app
import os

client = TestClient(app)

def write_version_file(content):
    '''Helper function to write temporary version file'''
    with open("../version.txt", "w", encoding="utf-8") as f:
        f.write(content)


def remove_version_file():
    '''Helper function to remove version file'''
    try:
        os.remove("../version.txt")
    except FileNotFoundError:
        pass


def test_version_normal():
    '''Function tests normal version file'''
    write_version_file("1.0.0\n")
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "1.0.0"}
    remove_version_file()


def test_version_empty():
    '''Function tests empty version file'''
    write_version_file("")
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": ""}
    remove_version_file()


def test_version_missing():
    '''Function tests version file not found edge case'''
    remove_version_file()
    with pytest.raises(FileNotFoundError):
        client.get("/version")


def test_version_strip():
    '''Function tests whitespace stripping'''
    write_version_file("   2.3.4  \n")
    response = client.get("/version")
    assert response.json() == {"version": "2.3.4"}
    remove_version_file()
