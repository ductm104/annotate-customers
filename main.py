import os
import sys
import cv2
import glob
import dash
import json
import base64

import numpy as np
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Hello'


class Scanner:
    def __init__(self, root='./data'):
        self.root = root
        self.json_path = os.path.join(root, 'label.json')
        os.system(f"cp {self.json_path} {os.path.join(root, 'prev_label.json')} 2>/dev/null")
        self.cur_id = 0
        self._scan()

    def _scan(self):
        self.folders = glob.glob(os.path.join(self.root, '*'))
        self.length = len(self.folders)

        try:
            with open(self.json_path, 'r') as file:
                self.data = json.load(file)
            print(self.data)
        except:
            print("New one")
            self.data = {}

    def _read_img(self, path):
        img = cv2.imread(path)
        img = cv2.resize(img, (224, 224))
        return img

    def _save(self):
        with open(self.json_path, 'w') as file:
            json.dump(self.data, file)

    def get_next(self, counter):
        self.cur_id = (self.cur_id+counter) % self.length
        folder = self.folders[self.cur_id]
        img_paths = glob.glob(os.path.join(folder, '*.jpg'))
        imgs = [self._read_img(path) for path in img_paths]
        label = self.data.get(str(self.folders[self.cur_id]), 0)
        return imgs, label

    def get_pos(self):
        return f'{self.cur_id+1:02d}/{self.length:02d}'

    def update(self, label):
        print('Update', self.cur_id, label)
        self.data[str(self.folders[self.cur_id])] = label
        self._save()


app.layout = html.Div([
    html.Div(
        children=[
            dbc.Button('Prev', color='secondary', id='prev-item', n_clicks=0, style={'marginRight': '10px'}),
            dbc.Button('Next', color='secondary', id='next-item', n_clicks=0, style={'marginLeft': '10px'}),
        ],
        style={'textAlign': 'center'}
    ),
    html.Hr(),
    html.Div(
        children=[
            dbc.RadioItems(
                id='radio',
                options=[
                    {'label': 'Employee', 'value': 'employee'},
                    {'label': 'Customer', 'value': 'customer'},
                ],
                value='employee',
                inline=True,
            )
        ],
        style={'textAlign': 'center'}
    ),
    html.Div(id='images', style={'textAlign': 'center', 'marginTop': '20px'}),
    html.Div(id='trash')
])


@app.callback(
        Output('images', 'children'),
        Output('radio', 'value'),
        [Input('next-item', 'n_clicks'),
         Input('prev-item', 'n_clicks')])
def update_imgs(btn1, btn2):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'next-item' in changed_id:
        counter = 1
    elif 'prev-item' in changed_id:
        counter = -1
    else:
        counter = 0

    imgs, label = scanner.get_next(counter)
    imgs = [cv2.imencode('.jpg', img)[1].tobytes() for img in imgs]
    out = [html.H4(scanner.get_pos())]
    for img in imgs:
        src = 'data:image/jpeg;base64,{}'.format(base64.b64encode(img).decode('utf-8'))
        out.append(html.Img(src=src))
    if label == 0:
        value = 'employee'
    else:
        value = 'customer'
    return out, value


@app.callback(
        Output('trash', 'children'),
        [Input('radio', 'value')])
def update_imgs(value):
    if value == 'employee':
        scanner.update(0)
    else:
        scanner.update(1)
    return []


if __name__ == '__main__':
    scanner = Scanner()
    app.run_server(host='0.0.0.0', port=5000, debug=False)
