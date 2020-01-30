from waitress import serve
import flaski
serve(flaski.app, host='0.0.0.0', port=8080)