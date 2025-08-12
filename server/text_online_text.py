import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_auth(token):
    url = f"{BASE_URL}/auth"
    resp = requests.post(url, json={"token": token})
    print("/auth:", resp.json())

def test_get_image(filename):
    url = f"{BASE_URL}/get_image?filename={filename}"
    resp = requests.get(url)
    print(f"/get_image ({filename}):", resp.status_code)
    if resp.status_code == 200:
        with open(f"test_{filename}", "wb") as f:
            f.write(resp.content)
        print(f"图片已保存为 test_{filename}")

def test_upload_classified(token, img_list):
    url = f"{BASE_URL}/upload_classified"
    classified = {img: [
        {"category": "清洗", "user_id": token}
    ] for img in img_list}
    data = {"user_id": token, "classified": classified}
    resp = requests.post(url, json=data)
    print("/upload_classified:", resp.json())

if __name__ == "__main__":
    # 自动读取token.txt中的第二个Token（跳过第一行）
    with open("token.txt", "r") as f:
        f.readline()  # 跳过第一行
        test_token = f.readline().strip()  # 读取第二行
    print(f"使用Token: {test_token}")
    test_auth(test_token)

    # 使用项目中存在的测试图片
    test_img = "p4_1040.png"
    print(f"使用测试图片: {test_img}")
    test_get_image(test_img)

    # 测试分类结果提交
    test_upload_classified(test_token, [test_img])


