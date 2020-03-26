import streamlit as st
import pandas as pd

from typing import Tuple, List
from functools import lru_cache
from countryinfo import CountryInfo
from .constants import (COUNTRIES_TRANSLATE_TO_COUNTRYINFO,
                        FILLNA)


@st.cache
def read_and_format_covid_datasets(url: str,
                                   case_types: List[str],
                                   id_vars: List[str],
                                   var_name: str,
                                   value_name: str) -> Tuple[pd.DataFrame, ...]:
    return tuple(reformat_data(df=pd.read_csv(url.format(case)),
                               id_vars=id_vars,
                               var_name=var_name,
                               value_name=value_name,
                               case_type=case) for case in case_types)


@lru_cache(maxsize=200)
def get_country_population_and_continent(country: str, ) -> Tuple[int, str]:
    try:
        country_translated = (
            country if country not in COUNTRIES_TRANSLATE_TO_COUNTRYINFO.keys()
            else COUNTRIES_TRANSLATE_TO_COUNTRYINFO[country]
        )

        country_translated_info = CountryInfo(country_translated)
        population = country_translated_info.population()
        continent = country_translated_info.region()
    except KeyError:
        population, continent = -1, FILLNA

    return population, continent


def reformat_data(df: pd.DataFrame, id_vars: [str], var_name: str,
                  value_name: str, case_type: str) -> pd.DataFrame:
    df_reformatted = pd.melt(df,
                             id_vars=id_vars,
                             var_name=var_name,
                             value_name=value_name)

    df_reformatted['Type'] = case_type
    df_reformatted['Date'] = pd.to_datetime(df_reformatted['Date'],
                                            infer_datetime_format=True)

    df_reformatted['Population/Continent'] = (
        df_reformatted['Country/Region']
        .apply(get_country_population_and_continent)
    )

    df_reformatted['Population'] = (df_reformatted['Population/Continent']
                                    .str
                                    .get(0))

    df_reformatted['Continent'] = (df_reformatted['Population/Continent']
                                   .str
                                   .get(1))

    return (
        df_reformatted
        .rename(columns={'Province/State': 'province_or_state',
                         'Country/Region': 'country_or_region',
                         'Lat': 'lat',
                         'Long': 'lon',
                         'Cases': 'cases',
                         'Type': 'type',
                         'Date': 'date',
                         'Population': 'population',
                         'Continent': 'continent'})
        .drop(columns='Population/Continent')
    )


@st.cache
def union_all_cases_types(df_confirmed: pd.DataFrame,
                          df_deaths: pd.DataFrame,
                          df_recovered: pd.DataFrame) -> pd.DataFrame:
    df_union_all = pd.concat([df_confirmed, df_deaths, df_recovered])
    df_union_all['type_order'] = (
        df_union_all['type']
        .apply(lambda x: 1 if x == 'confirmed' else 2 if 'deaths' else 3)
    )

    return df_union_all


@st.cache
def format_data_from_case_n(df: pd.DataFrame,
                            groupby: str,
                            n: int) -> pd.DataFrame:
    first_date_grouped = (
        df[(df['type'] == 'confirmed') & (df['cases'] >= n)]
        .groupby(groupby)
        .date
        .first()
        .reset_index()
        .rename(columns=dict(date=f'date_{n}'))
        .assign(**{f'days_from_{n}': lambda _: 1})
    )

    df_merged = df.merge(first_date_grouped,
                         on=groupby,
                         how='left')

    df_merged_filtered = (
        df_merged[df_merged['date'] >= df_merged[f'date_{n}']].copy()
    )

    df_merged_filtered[f'days_from_{n}'] = (df_merged_filtered[f'days_from_{n}']
                                            .fillna(1))

    df_merged_filtered[f'days_from_{n}'] = (
        df_merged_filtered
        .groupby([groupby, 'type'])
        [f'days_from_{n}']
        .transform('cumsum')
    )

    return df_merged_filtered


@st.cache
def format_data_from_case_n(df: pd.DataFrame,
                            groupby: str,
                            n: int,
                            my_type: str = 'confirmed') -> pd.DataFrame:
    first_date_grouped = (
        df[(df['type'] == my_type) & (df['cases'] >= n)]
        .groupby(groupby)
        .date
        .first()
        .reset_index()
        .rename(columns=dict(date=f'date_{n}'))
        .assign(**{f'days_from_{n}': lambda _: 1})
    )

    df_merged = df.merge(first_date_grouped,
                         on=groupby,
                         how='left')

    df_merged_filtered = (
        df_merged[df_merged['date'] >= df_merged[f'date_{n}']].copy()
    )

    df_merged_filtered[f'days_from_{n}'] = (df_merged_filtered[f'days_from_{n}']
                                            .fillna(1))

    df_merged_filtered = (df_merged_filtered
                          .astype({'date': 'datetime64[ns]'})
                          .sort_values(by=[groupby, 'type', 'date'])
                          .reset_index())

    df_merged_filtered[f'days_from_{n}'] = (
        df_merged_filtered
        .groupby([groupby, 'type'])
        [f'days_from_{n}']
        .transform('cumsum')
    )

    return df_merged_filtered


def max_summary_by_country(df: pd.DataFrame, columns: [str]) -> pd.DataFrame:
    return (df
            .groupby(['country_or_region', 'type'])
            [columns]
            .max())
