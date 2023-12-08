import os
import requests
from urllib.parse import urlparse, parse_qs, urljoin
from bs4 import BeautifulSoup
import chardet

def get_available_filename(file_path):
    base, ext = os.path.splitext(file_path)
    index = 1
    while os.path.exists(file_path):
        file_path = f"{base} ({index}){ext}"
        index += 1
    return file_path

def download_image(image_url, download_path=".", user_agent=None):
    try:
        headers = {'User-Agent': user_agent} if user_agent else {}
        response = requests.get(image_url, stream=True, headers=headers)
        response.raise_for_status()

        # Content-Disposition 헤더에서 파일명 추출 시도
        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition:
            encoding_guess = chardet.detect(content_disposition.encode())
            filename = content_disposition.split("filename=")[-1].strip('"; ')
            filename = filename.encode('latin1').decode('euc-kr')
        else:
            # Content-Disposition 헤더가 없을 경우 URL에서 파일명 추출
            query_params = parse_qs(urlparse(image_url).query)
            file_id = query_params.get('fileId', [''])[0]
            cntnts_sn = query_params.get('cntntsSn', [''])[0]
            filename = f"{file_id}_{cntnts_sn}.jpg"

        # 중복된 파일명을 피하기 위해 파일명을 조정
        full_path = os.path.join(download_path, filename)
        adjusted_filename = get_available_filename(full_path)

        # 추출한 파일명으로 이미지 저장
        with open(adjusted_filename, 'wb') as img_file:
            for chunk in response.iter_content(chunk_size=128):
                img_file.write(chunk)

        print(f"이미지 다운로드가 완료되었습니다. 파일명: {adjusted_filename}")
    except requests.exceptions.RequestException as e:
        print(f"이미지 다운로드 실패: {e}")

def extract_mobile_image_urls(url, user_agent=None):  # User-Agent를 매개변수로 추가
    try:
        headers = {'User-Agent': user_agent} if user_agent else {}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        image_urls = []
        for img_tag in soup.find_all('img'):
            src = img_tag.get('src')
            if src:
                absolute_url = urljoin(url, src)
                image_urls.append(absolute_url)

        return image_urls
    except requests.exceptions.RequestException as e:
        print(f"페이지 추출 실패: {e}")
        return []

def get_directory_name(url, user_agent):
    # URL에서 ".do" 이전의 부분 추출
    path = urlparse(url).path
    directory_name = os.path.splitext(os.path.basename(path))[0]

    # User-Agent에 따라 디바이스 구분
    if "/m/" in url:
        user_device = "Mobile"
        directory_name = f"[MO]{directory_name}"
    else:
        user_device = "PC"
        directory_name = f"[PC]{directory_name}"

    return user_device, directory_name

if __name__ == "__main__":
    # User-Agent 설정
    user_agent_mobile = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
    user_agent_pc = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    while True:
        user_input = input("사용자 입력 (0: 종료, URL: 이미지 다운로드): ")
        
        if user_input == '0':
            print("프로그램을 종료합니다.")
            break
        elif user_input.startswith('http'):
            # 사용자가 입력한 URL에서 디바이스 및 디렉토리 명 추출
            user_device, directory_name = get_directory_name(user_input, user_agent_mobile if "/m/" in user_input else user_agent_pc)

            # 이미지 URL 추출
            image_urls = extract_mobile_image_urls(user_input, user_agent_mobile if user_device == "Mobile" else user_agent_pc)

            # 디렉토리 생성
            local_download_path = os.path.join("downloaded_images", directory_name)

            if not os.path.exists(local_download_path):
                os.makedirs(local_download_path)

            # 추출된 이미지 URL로 다운로드 실행
            for url in image_urls:
                download_image(url, local_download_path, user_agent_mobile if user_device == "Mobile" else user_agent_pc)
        else:
            print("올바른 입력이 아닙니다. 다시 입력해주세요.")
