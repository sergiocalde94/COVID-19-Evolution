import streamlit as st
import locale

from helpers.constants import (CASE_TYPES,
                               FILLNA,
                               ID_VARS,
                               URL_DATA,
                               VALUE_NAME,
                               VAR_NAME)
from helpers.utils import (read_and_format_covid_datasets,
                           union_all_cases_types,
                           format_data_from_case_n,
                           max_summary_by_country)
from helpers.plotting import (plot_provinces_map_animated,
                              plot_figure_countries_facet,
                              plot_china_vs_europe_vs_us)


locale.setlocale(locale.LC_ALL, 'en_US.utf8')

df_confirmed, df_deaths, df_recovered = (
    read_and_format_covid_datasets(URL_DATA,
                                   CASE_TYPES,
                                   ID_VARS,
                                   VAR_NAME,
                                   VALUE_NAME)
)

df_all_cases = union_all_cases_types(df_confirmed, df_deaths, df_recovered)

df_all_cases_provinces = (df_all_cases
                          .fillna({'province_or_state': FILLNA})
                          .sort_values(['date', 'type_order']))

st.title(f'Coronavirus Disease (COVID-19) Evolution :hospital:')
st.text('The data is collected from Johns Hopkins University\'s repository')


st.markdown('Fork of https://github.com/sergiocalde94/COVID-19-Evolution, great job from my colleague [@sergiocalde94](https://twitter.com/sergiocalde94). '
''
'Now adapted to focus on death trends. Considering that confirmed "cases" depend a lot on the number of tests performed per country, their availability and the defined protocols. '
'More data on testing statistics per country: [ourworldindata](https://ourworldindata.org/coronavirus-testing-source-data), '
'[worldometer](https://www.worldometers.info/coronavirus/covid-19-testing/)')

plot_figure = plot_provinces_map_animated(df_all_cases_provinces)

st.subheader('Province/State Data Animated By Date :earth_africa:')

st.plotly_chart(plot_figure)

df_all_cases_countries = (df_all_cases_provinces
                          .groupby(['country_or_region', 'date', 'type'])
                          .agg(dict(cases='sum', population='first'))
                          .reset_index())

st.subheader('Country/Region Data To Compare :cityscape:')

min_number_cases = st.slider('Minimum number of deaths?',
                             min_value=1,
                             max_value=400,
                             value=10,
                             step=10)

df_all_cases_countries_from_case_n = (
    format_data_from_case_n(df_all_cases_countries,
                            groupby='country_or_region',
                            n=min_number_cases, mytype='Deaths')
)


countries_to_plot = st.multiselect(
    'Take one/various countries to plot the evolution of that country',
    sorted(df_all_cases_countries_from_case_n['country_or_region'].unique()),
    default=['China','Italy','Spain','US']
)

df_all_cases_countries_from_case_n_subset = (
    df_all_cases_countries_from_case_n[
        df_all_cases_countries_from_case_n['country_or_region']
        .isin(countries_to_plot)
    ]
)

if countries_to_plot:
    type_graph = st.radio(
        'What type of graph do you prefer?',
        (f'Cumulative deaths from death {min_number_cases}',
         f'New deaths per day from death {min_number_cases}'))

    st.warning(
        'Be careful when comparing two countries with very diferent population!'
    )

    log_scale_countries = st.checkbox('Log Scale Countries Comparation')

    population_weighting = st.checkbox(
        'Weighting By Population (Cases By 1 Million Population)'
    )

    if population_weighting:
        df_all_cases_countries_from_case_n_subset['cases'] = (
                df_all_cases_countries_from_case_n_subset['cases']
                / df_all_cases_countries_from_case_n_subset['population']
                * 1e6
        )
    cumulative = (type_graph == f'Cumulative deaths from death {min_number_cases}')
    if cumulative:
        df_countries_from_case_n_info = (
            max_summary_by_country(
                df_all_cases_countries_from_case_n_subset,
                columns=['cases', f'days_from_{min_number_cases}']
            )
        )

    figure = plot_figure_countries_facet(
                df_all_cases_countries_from_case_n_subset,
                population_type='country_or_region',
                min_number_cases=min_number_cases,
                log_scale=log_scale_countries,
                cumulative=cumulative,
                mytype='Deaths'
    )

    st.plotly_chart(figure)

st.markdown('More info: ')
st.markdown('* mortality rate estimation and age distribution: https://medium.com/@andreasbackhausab/coronavirus-why-its-so-deadly-in-italy-c4200a15a7bf, https://www.epicentro.iss.it/coronavirus/bollettino/Infografica_17marzo%20ITA.pdf')
st.markdown('* epidemic simulator: https://gabgoh.github.io/COVID/index.html')
st.markdown('* Dashboard of the COVID-19 Virus Outbreak in Singapore, with detail of all confirmed cases: https://co.vid19.sg/dashboard')
