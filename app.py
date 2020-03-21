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
                              plot_figure_countries_facet_cumulative,
                              plot_figure_countries_facet_new_cases_per_day,
                              plot_china_vs_europe_vs_us,
                              plot_figure_countries_facet)


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
st.text('First it shows an animated global vision over time')
st.text('Then you can focus on the countries you want')

plot_figure = plot_provinces_map_animated(df_all_cases_provinces)

st.subheader('Province/State Data Animated By Date :earth_africa:')

st.plotly_chart(plot_figure)

df_all_cases_countries = (df_all_cases_provinces
                          .groupby(['country_or_region', 'date', 'type'])
                          .agg(dict(cases='sum', population='first'))
                          .reset_index())

interest_link_one = 'https://ourworldindata.org/coronavirus-testing-source-data'
interest_link_two = ('https://www.worldometers.info/coronavirus/'
                     'covid-19-testing/')

st.markdown('By default this app show the info at cases level, but maybe it´s '
            'more correct to focus on death trends. Considering that confirmed '
            'cases depend a lot on the number of tests performed per country, '
            'their availability and the defined protocols.')

st.markdown('More data on testing statistics per country: '
            f'[ourworldindata]({interest_link_one}), '
            f'[worldometer]({interest_link_two})')

st.subheader('Country/Region Data To Compare :cityscape:')

death_trends = st.checkbox('Death trends')

min_number_cases = st.slider('Minimum number of '
                             f'{"cases" if not death_trends else "deaths"}?',
                             min_value=1,
                             max_value=400,
                             value=100 if not death_trends else 10,
                             step=10)

china_vs_europe_vs_eu_show = st.checkbox(
    'Show China, Europe And US Comparation'
)

if china_vs_europe_vs_eu_show:
    china_vs_europe_vs_us_log_scale = st.checkbox(
        'Log Scale China VS Europe VS US'
    )

    st.subheader(
        'China :flag-cn:, Europe :flag-eu: And US :flag-us: Comparation'
    )

    figure_china_vs_europe_vs_us = plot_china_vs_europe_vs_us(
        df_all_cases_provinces,
        min_number_cases=min_number_cases,
        log_scale=china_vs_europe_vs_us_log_scale,
        my_type='Confirmed' if not death_trends else 'Deaths'
    )

    st.plotly_chart(figure_china_vs_europe_vs_us)

df_all_cases_countries_from_case_n = (
    format_data_from_case_n(df_all_cases_countries,
                            groupby='country_or_region',
                            n=min_number_cases,
                            my_type=('Confirmed' if not death_trends
                                     else "Deaths"))
)

countries_to_plot = st.multiselect(
    'Take one/various countries to plot the evolution of that country',
    sorted(df_all_cases_countries_from_case_n['country_or_region'].unique()),
    default=['China', 'Italy', 'Spain', 'US']
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
        (f'Cumulative cases from case {min_number_cases}',
         f'New cases per day from case {min_number_cases}'))

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

    cumulative = (
            (type_graph == f'Cumulative deaths from death {min_number_cases}')
            | (type_graph == f'Cumulative cases from case {min_number_cases}')
    )

    if cumulative:
        df_countries_from_case_n_info = (
            max_summary_by_country(
                df_all_cases_countries_from_case_n_subset,
                columns=['cases', f'days_from_{min_number_cases}']
            )
        )

        if not death_trends:
            figure_cumulative = plot_figure_countries_facet_cumulative(
                df_all_cases_countries_from_case_n_subset,
                population_type='country_or_region',
                min_number_cases=min_number_cases,
                log_scale=log_scale_countries
            )

            st.plotly_chart(figure_cumulative)
    else:
        if not death_trends:
            figure_new_cases = plot_figure_countries_facet_new_cases_per_day(
                df_all_cases_countries_from_case_n_subset,
                min_number_cases=min_number_cases,
                log_scale=log_scale_countries
            )

            st.plotly_chart(figure_new_cases)

    if death_trends:
        death_figure = plot_figure_countries_facet(
            df_all_cases_countries_from_case_n_subset,
            min_number_cases=min_number_cases,
            log_scale=log_scale_countries,
            cumulative=cumulative,
            my_type='Deaths'
        )

        st.plotly_chart(death_figure)

interest_link_three = ('https://medium.com/@andreasbackhausab/'
                       'coronavirus-why-its-so-deadly-in-italy-c4200a15a7bf')

interest_link_four = ('https://www.epicentro.iss.it/coronavirus/bollettino/'
                      'Infografica_17marzo%20ITA.pdf')

interest_link_five = 'https://gabgoh.github.io/COVID/index.html'
interest_link_six = 'https://co.vid19.sg/dashboard'

st.markdown('More info: ')
st.markdown(
    f'* [Mortality rate estimation]({interest_link_three}) and '
    f'[age distribution]({interest_link_four})'
)

st.markdown(f'* [Epidemic simulator]({interest_link_five})')
st.markdown(
    f'* [Dashboard of the COVID-19 Virus Outbreak in Singapore]'
    f'({interest_link_six}), with detail of all confirmed cases'
)
