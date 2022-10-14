import pandas as pd


def get_citation_count_in_span(row, TIMESPAN):
    if row.citation_histogram is None:
        return row.cited_by
    else:
        return sum(map(lambda x: x[1],
                       filter(lambda x: x[0] <= row.year+TIMESPAN, row.citation_histogram)))


def get_tooltip(row, publications):
    papers = publications[(publications.year == row.year) &
                          (publications.citations_in_timespan == row.citations_in_timespan)]
    html = []
    for p in papers.iterrows():
        html += [
            f"""<div>
                    <b>Title:</b> {p[1].title}<br>
                    <b>Authors:</b> {", ".join(p[1].authors)}<br>
                    <b>Total Citations:</b> {p[1].cited_by}
                </div>"""]
    return pd.Series([len(papers),
                     dict(papers[['title', 'authors', 'cited_by']]),
                     f"""<div>{'<hr>'.join(html)}</div>"""])


def process_data(DATA, TIMESPAN, EARLIEST, LATEST, PROPER_YEARS):
    if DATA:
        publications = pd.DataFrame(DATA['publications'])
        publications = publications[(publications.year >= EARLIEST) &
                                    (publications.year <= LATEST)]
        publications['cited_by'] = publications['cited_by'].fillna(0)
        publications = publications.astype({'year': 'int',
                                            'cited_by': 'int'})
        first_publication = publications.year.min()

        author = pd.DataFrame({'keys': ['AuthorID', 'Name', 'Interests', 'Citations', 'h-index', 'i10-index'],
                               'values': [DATA['authorID'], DATA['name'], ', '.join(DATA['interests']),
                                          DATA['citations'], DATA['hindex'], DATA['i10index']]})

        publications['citations_in_timespan'] = publications.apply(lambda row: get_citation_count_in_span(row,
                                                                                                          TIMESPAN),
                                                                   axis=1)
        dots = publications[['year', 'citations_in_timespan']
                            ].drop_duplicates().sort_values(['year', 'citations_in_timespan'], ascending=True)
        dots['career_year'] = dots.year-first_publication
        dots[['papers_count', 'papers', 'tooltip_text']] = dots.apply(lambda row: get_tooltip(row,
                                                                                              publications),
                                                                      axis=1)
        dots['view_year'] = dots['year'] if PROPER_YEARS else dots['career_year']
        dots = dots[['view_year', 'year', 'career_year',
                     'citations_in_timespan', 'papers_count',
                     'papers', 'tooltip_text']]

        lines = dots.groupby(['view_year',
                              'year',
                              'career_year']).agg(max_citations_in_timespan=('citations_in_timespan', 'max')).reset_index()
    else:
        author = pd.DataFrame(columns=['keys', 'values'])
        dots = pd.DataFrame(columns=['view_year', 'year', 'career_year',
                                     'citations_in_timespan', 'papers_count',
                                     'papers', 'tooltip_text'])
        lines = pd.DataFrame(columns=['view_year', 'year', 'career_year',
                                      'max_citations_in_timespan'])

    return author, dots, lines
