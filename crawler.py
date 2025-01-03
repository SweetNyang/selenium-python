from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import os
from dotenv import load_dotenv
import mysql.connector
load_dotenv()


def connect_to_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def save_store_to_db(store_link, store_name, category, address, phone_num, business_hours):
    db = connect_to_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO stores (store_link, store_name, category, address, phone_num, business_hours)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (store_link, store_name, category, address, phone_num, business_hours))
        store_id = cursor.lastrowid
        db.commit()
        print("DB 저장 성공:", (store_link, store_name, category, address, phone_num, business_hours))
        return store_id
    except Exception as e:
        print(f"DB 저장 중 오류 발생: {e}")
    finally:
        cursor.close()
        db.close()

def save_menu_to_db(store_id, menu_name, menu_description, menu_image, menu_price):
    db = connect_to_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO menus (store_id, menu_name, menu_description, menu_image, menu_price)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (store_id, menu_name, menu_description, menu_image, menu_price))
        db.commit()
        print(f"메뉴 저장 성공: {menu_name}")
    except Exception as e:
        print(f"메뉴 저장 중 오류 발생: {e}")
    finally:
        cursor.close()
        db.close()

# iframe으로 왼쪽 포커스 맞추기
def switch_left():
    driver.switch_to.parent_frame()
    iframe = driver.find_element(By.XPATH,'//*[@id="searchIframe"]')
    driver.switch_to.frame(iframe)

# iframe으로 오른쪽 포커스 맞추기    
def switch_right():
    driver.switch_to.parent_frame()
    iframe = driver.find_element(By.XPATH,'//*[@id="entryIframe"]')
    driver.switch_to.frame(iframe)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="zD5Nm undefined"]')))

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

options = webdriver.ChromeOptions()
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
options.add_argument('window-size=1380,900')
driver = webdriver.Chrome(options=options)

# 대기 시간
driver.implicitly_wait(time_to_wait=3)

# 반복 종료 조건
loop = True

URL = 'https://map.naver.com/p/search/%EA%B1%B4%EB%8C%80%20%EB%94%94%EC%A0%80%ED%8A%B8?c=12.00,0,0,0,dh'
driver.get(url=URL)

    
while(True):
    switch_left()

    # 페이지 숫자를 초기에 체크 [ True / False ]
    try:
        next_page = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[@class="eUTV2" and @aria-disabled="false"]'))
        ).get_attribute('aria-disabled')
    except Exception as e:
        print("요소를 찾는 중 오류 발생:", e)
        next_page = 'true'  # 기본값 설정
    
    if(next_page == 'true'):
        break

    ############## 맨 밑까지 스크롤 ##############
    scrollable_element = driver.find_element(By.CLASS_NAME, "Ryr1F")

    last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_element)

    while True:
        # 요소 내에서 아래로 600px 스크롤
        driver.execute_script("arguments[0].scrollTop += 600;", scrollable_element)

        # 페이지 로드를 기다림
        sleep(1)  # 동적 콘텐츠 로드 시간에 따라 조절

        # 새 높이 계산
        new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_element)

        # 스크롤이 더 이상 늘어나지 않으면 루프 종료
        if new_height == last_height:
            break

        last_height = new_height


    ############## 현재 page number 가져오기 - 1 페이지 ##############

    page_no = driver.find_element(By.XPATH,'//a[contains(@class, "mBN2s qxokY")]').text

    # 현재 페이지에 등록된 모든 가게 조회
    # 첫페이지 광고 2개 때문에 첫페이지는 앞 2개를 빼야함
    if(page_no == '1'):
        elemets = driver.find_elements(By.XPATH,'//*[@id="_pcmap_list_scroll_container"]//li')[2:]
    else:
        elemets = driver.find_elements(By.XPATH,'//*[@id="_pcmap_list_scroll_container"]//li')

    print('현재 ' + '\033[95m' + str(page_no) + '\033[0m' + ' 페이지 / '+ '총 ' + '\033[95m' + str(len(elemets)) + '\033[0m' + '개의 가게를 찾았습니다.\n')

    for index, e in enumerate(elemets, start=1):
        final_element = e.find_element(By.CLASS_NAME,'CHC5F').find_element(By.XPATH, ".//a/div/div/span")

        print(str(index) + ". " + final_element.text)

    print(Colors.RED + "-"*50 + Colors.RESET)

    switch_left()

    sleep(2)

    for index, e in enumerate(elemets, start=1):
        
        store_name = '' # 가게 이름
        category = '' # 카테고리
        address = '' # 가게 주소
        business_hours = [] # 영업 시간
        phone_num = '' # 전화번호

        switch_left()


        # 순서대로 값을 하나씩 클릭
        try:
            element_to_click = e.find_element(By.CLASS_NAME, 'CHC5F').find_element(By.XPATH, ".//a/div/div/span")
            driver.execute_script("arguments[0].scrollIntoView(true);", element_to_click)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element_to_click))
            driver.execute_script("arguments[0].click();", element_to_click)
        except Exception as click_err:
            print(f"{Colors.RED}클릭 오류 발생: {click_err}{Colors.RESET}")
            continue

        sleep(2)

        switch_right()

        ################### 여기부터 크롤링 시작 ##################

        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[@class="GHAhO"]'))
        )
        
        # 가게 이름 추출
        store_name = title_element.text
        print(f"가게 이름: {store_name}")

        # 카테고리 추출
        category_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@id="_title"]//span[@class="lnJFt"]'))
        )
        category = category_element.text
        print(f"카테고리: {category}")

        allowed_categories = ["베이커리", "카페", "디저트", "케이크", "아이스크림", "와플"]
        if not any(cat in category for cat in allowed_categories):
            continue  # 허용된 카테고리가 아닐 경우 스킵

        # 가게 링크 추출
        share_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@id="_btp.share"]'))
        )
        ActionChains(driver).move_to_element(share_button).click(share_button).perform()
        print("공유 버튼 클릭 완료")

        share_link_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@class, "_spi_copyurl_txt")]'))
        )
        store_link = share_link_element.get_attribute('href')
        print(f"공유 링크: {store_link}")

        # 공유 창 닫기
        close_button = WebDriverWait(driver, 10).until(
           EC.element_to_be_clickable((By.XPATH, '//span[@class="_spi_cls spim" and text()="닫기"]'))
        )  
        close_button.click()

        # 가게 주소
        address = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[@class="LDgIH"]'))
        ).text
        print(f"주소: {address}")

        try:
            # 스크롤 내리기 (300px 아래로 이동)
            scroll_step = 300
            driver.execute_script(f"window.scrollBy(0, {scroll_step});")
            sleep(1)  # 스크롤 후 로딩 대기

           # "펼쳐보기" 버튼 찾기
            unfold_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="y6tNq"]//span[@class="place_blind" and text()="펼쳐보기"]'))
            )

            # JavaScript로 클릭 강제 실행
            driver.execute_script("arguments[0].click();", unfold_button)
            print("펼쳐보기 버튼 클릭 완료")

            # 2초 대기 (더보기 로드 반영)
            sleep(2)

             # 영업시간 텍스트 크롤링
            business_hours = []  # 결과 저장용 리스트
            business_blocks = driver.find_elements(By.XPATH, '//div[@class="w9QyJ"]')

            for block in business_blocks:
                try:
                    # 요일 크롤링
                    day = block.find_element(By.XPATH, './/span[@class="i8cJw"]').text

                    # 시간 크롤링
                    time_info = block.find_element(By.XPATH, './/div[@class="H3ua4"]').text

                    # 결과 저장
                    business_hours.append(f"{day}: {time_info}")
                except Exception as inner_e:
                    print(f"영업시간 블록 처리 중 오류 발생: {inner_e}")
            
            # 텍스트 출력
            for hour in business_hours:
                print(hour)

            # 가게 전화번호
            phone_num = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//span[@class="xlx7Q"]'))
            ).text
            print(f"전화번호: {phone_num}")

            # 함수 호출
            store_id = save_store_to_db(store_link, store_name, category, address, phone_num, "\n".join(business_hours))

            # 메뉴 탭 클릭
            menu_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "_tab-menu") and .//span[text()="메뉴"]]'))
            )
            menu_tab.click()
            print("메뉴 탭 클릭 완료")
    
            # 메뉴 정보 크롤링
            menu_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[@class="MXkFw"] | //div[@class="info_detail"]'))
            )

            image_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[@class="YBmM2"] | //div[@class="info_img"]'))
            )

            for idx, menu in enumerate(menu_items):
                # 스크롤
                driver.execute_script("arguments[0].scrollIntoView(true);", menu)

                # 메뉴 이름
                try:
                    menu_name = menu.find_element(By.XPATH, './/span[@class="lPzHi"] | .//div[@class="tit"]').text
                except Exception:
                    menu_name = "메뉴 이름 없음"

                # 메뉴 설명
                try:
                    menu_description = menu.find_element(By.XPATH, './/div[@class="kPogF"] | .//span[@class="detail_txt"]').text
                except Exception:
                    menu_description = "설명 없음"

                # 메뉴 가격
                try:
                    price_elements = menu.find_elements(By.XPATH, './/div[@class="GXS1X"]/em | .//div[@class="price"]')
                    if price_elements:  # 가격 정보가 있는 경우
                    
                        menu_price_list = [price.text for price in price_elements]
                        if "변동" in menu_price_list:
                            menu_price = "변동"
                        if "무료" in menu_price_list:
                            menu_price = "무료"
                        else:
                            menu_price = " ~ ".join(menu_price_list)  # 가격 범위 저장
                    else:
                        # 가격 정보가 없는 경우
                        price_text_element = menu.find_element(By.XPATH, './/div[@class="GXS1X"] | .//div[@class="price"]').text
                        if "변동" in price_text_element:
                            menu_price = "변동"
                        if "무료" in price_text_element:
                            menu_price = "무료"
                        else:
                            menu_price = "가격 정보 없음"
                except Exception:
                    menu_price = "가격 정보 없음"

                # 메뉴 이미지
                try:
                    menu_image = image_items[idx].find_element(By.XPATH, './/div[@class="place_thumb"]/img[@class="K0PDV"] | .//span[@class="img_box"]/img').get_attribute('src')
                except Exception:
                    menu_image = "이미지 없음"

                # 출력
                print(f"가게 id: {store_id}")
                print(f"메뉴 이름: {menu_name}")
                print(f"설명: {menu_description}")
                print(f"가격: {menu_price}")
                print(f"이미지: {menu_image}")

                save_menu_to_db(
                    store_id=store_id,  # 가게와 연결
                    menu_name=menu_name,
                    menu_description = menu_description,
                    menu_image=menu_image,
                    menu_price=menu_price
                )
                print("-" * 50)

        except Exception as e:
            print(f"크롤링 중 오류 발생: {e}")
    
    switch_left()
        
    # 페이지 다음 버튼이 활성화 상태일 경우 계속 진행
    if(next_page == 'false'):
        driver.find_element(By.XPATH,'//a[@class="eUTV2" and @aria-disabled="false"]').click()
    # 아닐 경우 루프 정지
    else:
        loop = False

