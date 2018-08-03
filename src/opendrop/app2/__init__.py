import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')


from opendrop.app2.app import OpendropApplication

if __name__ == '__main__':
    my_app = OpendropApplication()
    print('App starting...')
    print('App exited with {}'.format(my_app.run()))
