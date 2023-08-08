import matplotlib.font_manager
import os

if "Taipei Sans TC Beta" not in sorted([f.name for f in matplotlib.font_manager.fontManager.ttflist]):
    print('-----------------------------------')

    import matplotlib
    print(matplotlib.__file__.rsplit('__init__.py')[0])
    mat_init_path = f"{matplotlib.__file__.rsplit('__init__.py')[0]}/mpl-data/fonts/ttf"
    cmd = '''
    cp fonts/*.ttf  %(mat_init_path)s
    chmod 777 %(mat_init_path)s/*.ttf
    '''  % locals()
    os.system(cmd)

    cmd = '''
    if [ -d ~/.cache/.matplotlib ]
    then
        rm ~/.cache/.matplotlib/*
    elif  [ -d ~/.matplotlib/ ]
    then
        rm ~/.matplotlib/*json
    fi
    '''
    os.system(cmd)

    print("*****     Chinese font install sucessfully! ")
else:
    print("*****     Chinese font has already installed!  ")