import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # base directory
    BASEPATH = basedir
    APPPATH = basedir + '/app'
    # setup connection to SQLite data base
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'inkart_app.db')
