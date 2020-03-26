URL_DATA = ('https://raw.githubusercontent.com/'
            'CSSEGISandData/COVID-19/master/'
            'csse_covid_19_data/csse_covid_19_time_series/'
            'time_series_covid19_{}_global.csv')

COUNTRIES_TRANSLATE_TO_COUNTRYINFO = {
    'Czechia': 'Czech Republic',
    'North Macedonia': 'republic of macedonia',
    'US': 'United States',
    'Korea, South': 'South Korea',
    'Taiwan*': 'Taiwan'
}

CASE_TYPES = ['confirmed', 'deaths', 'recovered']
ID_VARS = ['Province/State', 'Country/Region', 'Lat', 'Long']
VAR_NAME = 'Date'
VALUE_NAME = 'Cases'
FILLNA = 'UNKNOWN'
