"""
Copyright (c) 2017 Genome Research Ltd.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <http://www.gnu.org/licenses/>.
"""
"""
Entry point for the handling of GitHub pushes.
"""
from bottle import request, response, Bottle

app = Bottle()


@app.route('/', method='POST')
def receive_github_push():
    return 'SUCCESS'


def run_server():
    app.run(host='0.0.0.0', port=8080, debug=True)  # Built-in Bottle development server.

if __name__ == '__main__':
    run_server()
