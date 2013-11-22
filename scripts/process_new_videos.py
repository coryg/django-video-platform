import os
import sys
import logging


def setup_environment():
	pathname = os.path.dirname(os.path.realpath(__file__))
	sys.path.append(os.path.normpath(os.path.join(os.path.abspath(pathname), '../')))
	sys.path.append(os.path.normpath(os.path.join(os.path.abspath(pathname), '../../')))
	os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Must set up environment before imports.
setup_environment()


from document.documentCleanUp import removeDocumentPendingDelete

def main(argv=None):

	try:
		removeDocumentPendingDelete()

	except Exception as exc:
		logging.exception(exc)


if __name__ == '__main__':
	main()