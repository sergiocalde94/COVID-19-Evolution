import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from plotly.graph_objects import Figure
from .constants import FILLNA
from .utils import format_data_from_case_n


@st.cache
def plot_provinces_map_animated(df_provinces: pd.DataFrame) -> Figure:
    df_provinces['date'] = df_provinces['date'].dt.strftime('%d %b %Y')
    df_provinces_with_cases = df_provinces[df_provinces['cases'] > 0].copy()

    df_provinces_with_cases['cases_log'] = (
        np.round(
            np.log10(df_provinces_with_cases['cases']),
            3
        )
    )

    df_provinces_with_cases['hover_name'] = (
        df_provinces_with_cases['province_or_state'].copy()
    )

    mask_provinces_unknown = (
            df_provinces_with_cases['province_or_state'] == FILLNA
    )

    df_provinces_with_cases.loc[mask_provinces_unknown, 'hover_name'] = (
        df_provinces_with_cases
        .loc[df_provinces_with_cases['province_or_state'] == FILLNA,
             'country_or_region']
    )

    return (
        px
        .scatter_geo(data_frame=df_provinces_with_cases,
                     lat='lat', lon='lon',
                     color='type', text='cases',
                     hover_name='hover_name', hover_data=['type', 'cases'],
                     custom_data=['cases_log'], size='cases_log',
                     animation_frame='date', opacity=.25,
                     projection='natural earth')
    )


def plot_figure_countries_facet_cumulative(df_countries: pd.DataFrame,
                                           population_type: str,
                                           min_number_cases: int,
                                           log_scale: bool) -> Figure:
    return (
        px
        .line(df_countries,
              x=f'days_from_{min_number_cases}', y='cases',
              color='type',
              facet_col='type',
              facet_row=population_type,
              log_y=log_scale)
        .for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    )


def plot_figure_countries_facet_new_cases_per_day(df_countries: pd.DataFrame,
                                                  min_number_cases: str,
                                                  log_scale: bool) -> Figure:
    df_countries_copy = df_countries.copy()

    df_countries_copy['cases'] = (
        df_countries_copy
        .groupby(['country_or_region', 'type'])
        .cases
        .transform(
            lambda group: group.rolling(2, min_periods=1).apply(
                lambda x: x if len(x) == 1 else x.diff().iloc[1]
            )
        )
    )

    return (
        px
        .line(df_countries_copy,
              x=f'days_from_{min_number_cases}', y='cases',
              color='type',
              facet_col='type',
              facet_row='country_or_region',
              log_y=log_scale)
        .for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    )


def plot_china_vs_europe_vs_us(df_provinces: pd.DataFrame,
                               min_number_cases: int,
                               log_scale: bool) -> Figure:
    df_provinces_filtered = (
        df_provinces[(df_provinces['continent'] == 'Europe')
                     | (df_provinces['country_or_region']
                        .isin(['China', 'US']))]
        .copy()
    )

    mask_european_countries = df_provinces_filtered['continent'] == 'Europe'

    df_european_countries_population = (
        df_provinces_filtered[mask_european_countries]
        .groupby(['country_or_region'])
        .population
        .first()
    )

    df_provinces_filtered.loc[mask_european_countries, 'population'] = (
        df_european_countries_population.sum()
    )

    df_provinces_filtered.loc[mask_european_countries, 'country_or_region'] = (
        'Europe'
    )

    df_provinces_grouped = (
        df_provinces_filtered
        .groupby(['country_or_region', 'date', 'type'])
        .agg(dict(cases='sum', population='first'))
        .reset_index()
    )

    df_provinces_filtered_formatted = format_data_from_case_n(
        df_provinces_grouped, groupby='country_or_region', n=min_number_cases
    )

    fig = (px
           .line(df_provinces_filtered_formatted,
                 x=f'days_from_{min_number_cases}', y='cases',
                 color='country_or_region',
                 facet_row='type',
                 log_y=log_scale)
           .for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])))

    fig.layout.yaxis2.update(matches=None)

    return fig
