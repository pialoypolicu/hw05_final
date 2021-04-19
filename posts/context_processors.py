from datetime import datetime as dt


def get_year_footer(request):
    year = dt.now().strftime('%Y')
    return {'year': year}
