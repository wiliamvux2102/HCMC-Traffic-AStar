import json
import re
import requests

API_URL = "https://giaothong.hochiminhcity.gov.vn/ajaxpro/HTDP.Library.AJAX.HTDPAjax,HTDP.Library.ashx"

# Sử dụng cookie bạn vừa trích xuất từ trình duyệt
cookies = {
    ".VDMS": "4B3D6214319EA863D3A41716D66DC3385FDDDBCE3489EFE1A34EEB46990D41E2E789323F5398533C4D0D4757D0676CF2BC6800F758066F541526952939ABB286ABA34F1C4496983C90C9D460E0D6D0CFCE79A840BFBB46BFD3601DD2A046C5176082B68AFD795A59375CE356571DCAF8B20786D3",
    "_ga": "GA1.3.1454316626.1789615107",
    "_ga_KYH7PYHKJT": "GS2.3.s1790415660$o1$g1$t1790415671$j49$l0$h0",
    "_gid": "GA1.3.219977091.1790654927",
    "_frontend": "!BBsyDVxc1LJorKHNM4rrCBRI9aIoG2DA9doS4xte2SwXZOW4fUPCKSd8DnRQeUAp13+W5mB3tP0+d94=",
    "TS01e7700a": "0150c7cfd14ae4ce7b601aa4c5a5272200c54d2b2c828a236fcd2c5deecfc122ccba81934cd2ffb46c10488551f858a36a68b1b60948b26461cf52eddb32077b7fedb6439b",
    "_pk_ref.1.2f14": "[\"\",\"\",1790662676,\"https://www.bing.com/\"]",
    "_pk_id.1.2f14": "a3619818d9504b8a.1789615117.7.1790662676.1790662676.",
    "_pk_ses.1.2f14": "*",
    "_gat": "1",
    "_ga_JCXT8BPG4E": "GS2.3.s1790662682$o7$g0$t1790662682$j60$l0$h0",
}

headers = {
    "Accept": "*/*",
    "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
    "Connection": "keep-alive",
    "Content-Type": "text/plain; charset=UTF-8",
    "Origin": "https://giaothong.hochiminhcity.gov.vn",
    "Referer": "https://giaothong.hochiminhcity.gov.vn/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36 Edg/154.0.0.0",
    "X-AjaxPro-Method": "GetLocationAlert",
    "sec-ch-ua": '"Chromium";v="154", "Microsoft Edge";v="154", "Not A(Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Lấy toàn bộ các trường thông tin mà hệ thống hỗ trợ
payload = {
    "fields": ["ID", "AreaDesc", "Speed", "Shape", "Radius", "Time"]
}

def download_all_data():
    print("[*] Đang gửi request tải toàn bộ dữ liệu giao thông...")
    try:
        response = requests.post(
            API_URL, 
            cookies=cookies, 
            headers=headers, 
            data=json.dumps(payload),
            timeout=25
        )
        print(f"[+] HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            raw_text = response.text
            # Loại bỏ phần vỏ bọc comment của AjaxPro
            cleaned = re.sub(r"^/\*.*?\*/", "", raw_text, flags=re.DOTALL).strip()
            if cleaned.endswith(";"):
                cleaned = cleaned[:-1].strip()

            parsed = json.loads(cleaned)
            data_list = parsed.get("value", parsed) if isinstance(parsed, dict) else parsed

            # Lưu toàn bộ dữ liệu ra file all_traffic_data.json
            with open("all_traffic_data.json", "w", encoding="utf-8") as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)

            print(f"[+] Đã tải và lưu thành công {len(data_list)} bản ghi vào 'all_traffic_data.json'!")
        else:
            print(f"[-] Máy chủ trả về mã lỗi: {response.status_code}")
            print(response.text[:200])

    except Exception as e:
        print(f"[-] Lỗi trong quá trình kết nối: {e}")

if __name__ == "__main__":
    download_all_data()