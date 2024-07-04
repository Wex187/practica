import requests
import psycopg2

# Получение списка регионов и городов
response = requests.get('https://api.hh.ru/areas')
areas = response.json()


def get_city_id(city_name, areas):
    city_name_lower = city_name.strip().lower()
    for country in areas:
        for area in country['areas']:
            if area['name'].strip().lower() == city_name_lower:
                return area['id']
            # Проверяем вложенные города
            if 'areas' in area:
                for city in area['areas']:
                    if city['name'].strip().lower() == city_name_lower:
                        return city['id']
                # Проверяем вложенные области/регионы
                for sub_area in area['areas']:
                    if sub_area['name'].strip().lower() == city_name_lower:
                        return sub_area['id']
    return None




def parse(area, keyword, page=0, per_page=100):
    url = 'https://api.hh.ru/vacancies'
    params = {
        'area': area,
        'text': keyword,
        'page': page,
        'per_page': per_page
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f'Не удалось получить данные: {response.status_code}')
        return []

    data = response.json()
    vacancies = []
    for item in data['items']:
        title = item['name']
        link = item['alternate_url']
        company = item['employer']['name']
        area = item['area']['name']
        salary_info = item['salary']

        if salary_info is None:
            salary = "Заработная плата не указана"
        else:
            salary_from = salary_info.get('from')
            salary_to = salary_info.get('to')
            salary_currency = salary_info.get('currency')
            salary_gross = salary_info.get('gross')

            salary = ''
            if salary_from:
                salary += f"от {salary_from} "
            if salary_to:
                salary += f"до {salary_to} "
            if salary_currency:
                salary += salary_currency
            if salary_gross:
                salary += " до вычета налогов" if salary_gross else " после вычета налогов"

        vacancies.append({
            'title': title,
            'link': link,
            'company': company,
            'area': area,
            'salary': salary.strip()
        })

    return vacancies


def sd(vacancies):
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="12365477S",
        database="vac",
    )
    cursor = conn.cursor()

    for vacancy in vacancies:
        cursor.execute("""
            SELECT 1 FROM vacancies WHERE link = %s
        """, (vacancy['link'],))

        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO vacancies (title, link, company, area, salary) VALUES (%s, %s, %s, %s, %s)
            """, (vacancy['title'], vacancy['link'], vacancy['company'], vacancy['area'], vacancy['salary']))

    conn.commit()
    cursor.close()
    conn.close()


def main():
    keyword = "Водитель"
    area = 'Санкт-Петербург'
    number_of_vacancies = 5
    city_id = get_city_id(area, areas)

    if city_id:
        vacancies = parse(city_id, keyword, per_page=number_of_vacancies)
        if vacancies:
            sd(vacancies)
            print(f'Сохранено {len(vacancies)} вакансий в базу данных')
        else:
            print('Вакансий не найдено')
    else:
        print(f'Город {area} не найден')


if __name__ == '__main__':
    main()
