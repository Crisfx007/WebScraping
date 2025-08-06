import csv
from newsapi import NewsApiClient
import jsonpath
from datetime import datetime

newsapi = NewsApiClient(api_key='')


def convert_iso_to_custom_format(iso_date):
    dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    return dt.strftime("%d-%m-%Y %H:%M:%S")


def extract_data_as_string(json_data, json_path):
    result = jsonpath.jsonpath(json_data, json_path)
    if result:
        return ', '.join(map(str, result))
    else:
        return ""


def extract_data_as_list(json_data, json_path):
    result = jsonpath.jsonpath(json_data, json_path)
    if result:
        return result
    else:
        return []


def save_articles_to_csv(articles, filename='.csv'):
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(['ID', 'Source', 'Content', 'Published At', 'URL'])

        for idx, a in enumerate(articles, start=1):
            source = extract_data_as_string(a, "source.name")
            content = extract_data_as_string(a, "description")
            content1 = extract_data_as_string(a, "content")
            content = content + " " + content1
            date_time = extract_data_as_string(a, "publishedAt")
            if date_time:
                date_time = convert_iso_to_custom_format(date_time)
            url = extract_data_as_string(a, "url")
            writer.writerow([idx, source, content, date_time, url])

    print(f"Articles saved to CSV at: {filename}")


for i in range(1, 5):
    articles_response = newsapi.get_everything(q='',
                                               from_param='2024-11-01',
                                               to='2022-12-12',
                                               language='en',
                                               sort_by='publishedAt',
                                               page=i)

    articles = extract_data_as_list(articles_response, "articles.*")
    if articles:
        save_articles_to_csv(articles)

print("Articles saved successfully.")


