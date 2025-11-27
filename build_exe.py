import PyInstaller.__main__
import os
import shutil

def build():
    print("Building Invoice Generator...")
    
    # Clean dist/build
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')

    # PyInstaller arguments
    args = [
        'src/main.py',
        '--name=InvoiceGenerator',
        '--windowed',
        '--onedir',
        '--noconfirm',
        # Include resources (fonts, logos)
        '--add-data=src/resources;src/resources',
        # Include schema
        '--add-data=src/db_schema.sql;src',
    ]
    
    PyInstaller.__main__.run(args)
    print("Build complete. Executable is in dist/InvoiceGenerator")

if __name__ == '__main__':
    build()
