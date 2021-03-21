from flask import Flask, render_template, request, url_for, send_from_directory, json, redirect, Response
import pathlib
from argparse import ArgumentParser
import parsers


TAGS_FILENAME = 'tags.txt'
IMAGES_TAGS_DIR = 'images_tags'


app = Flask(__name__)


def get_images_names():
    img_dir_path = app.config['img_dir_path']
    return [
        path.name for path in pathlib.Path(img_dir_path).iterdir()
        if path.suffix.lower() in ['.jpg', '.png', '.jpeg']
    ]


@app.route('/')
def home():
    img_names = get_images_names()
    if img_names:
        return render_template('tag_the_image.html', all_tags=app.config['all_tags'])
    else:
        return 'No images! Run the app in the directory containing your images!', 404


@app.route('/metadata')
def metadata():
    initial_img_name = sorted(get_images_names())[0]
    return redirect(url_for('tag_image', img_name=initial_img_name))


@app.route('/image/<path:img_name>', methods=['GET'])
def image(img_name):
    return send_from_directory(app.config['img_dir_path'], img_name)


@app.route('/tag_image/<path:img_name>', methods=['GET', 'POST'])
def tag_image(img_name):
    if request.method == 'POST':
        img_tags_file = (app.config['images_tags_dir_path'] / img_name).with_suffix('.txt')
        json_data = request.get_json()
        img_tags_file.open('w').write('\n'.join(json_data['chosen_tags']))
        return Response(status=200)
    else:
        img_tags_file = (app.config['images_tags_dir_path'] / img_name).with_suffix('.txt')
        chosen_tags = []
        if img_tags_file.exists():
            chosen_tags = img_tags_file.open().read().split()
        else:
            img_tags_file.touch()

        data = {
            'all_tags': app.config['all_tags'],
            'chosen_tags': chosen_tags,
            'actual_img_name': img_name,
        }
        return json.dumps(data)


@app.route('/tag_image/previous', methods=['GET'])
def previous():
    params = request.args
    img_names = sorted(get_images_names())
    actual_img_index = img_names.index(params['actual_img_name'])
    previous_img_name = img_names[(actual_img_index - 1) % len(img_names)]
    return redirect(url_for('tag_image', img_name=previous_img_name))


@app.route('/tag_image/next', methods=['GET'])
def next():
    params = request.args
    img_names = sorted(get_images_names())
    actual_img_index = img_names.index(params['actual_img_name'])
    next_img_name = img_names[(actual_img_index + 1) % len(img_names)]
    return redirect(url_for('tag_image', img_name=next_img_name))


@app.route('/export_to_csv', methods=['GET'])
def export_to_csv():
    import csv
    images_tags = app.config['images_tags_dir_path']
    csv_file_path = app.config['img_dir_path'] / 'tags_table.csv'
    all_tags = app.config['all_tags']
    with csv_file_path.open('w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['image_name'] + all_tags)
        for tags_file in images_tags.iterdir():
            tags = tags_file.open().read().split()
            new_row = [tags_file.stem] + [1 if tag in tags else 0 for tag in all_tags]
            writer.writerow(new_row)
    return Response(status=201)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('img_dir', help='path to the directory containing images')
    args = parser.parse_args()

    app.config['img_dir_path'] = pathlib.Path(args.img_dir)
    app.config['all_tags'] = (app.config['img_dir_path'] / TAGS_FILENAME).open().read().split()
    app.config['images_tags_dir_path'] = app.config['img_dir_path'] / IMAGES_TAGS_DIR
    if not app.config['images_tags_dir_path'].exists():
        app.config['images_tags_dir_path'].mkdir()

    app.run()
