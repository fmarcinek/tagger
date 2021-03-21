from flask import Flask, render_template, request, url_for, send_from_directory, json, redirect, Response
import pathlib
from argparse import ArgumentParser
import parsers


IMAGES_TAGS_DIR = 'images_tags'
app = Flask(__name__)


def get_images_names():
    img_dir_path = app.config['img_dir_path']
    return [
        path.name for path in pathlib.Path(img_dir_path).iterdir()
        if path.suffix.lower() in ['.jpg', '.png', '.jpeg']
    ]


def get_images_tags_file(img_name, tag_group):
    tags_file_name = pathlib.Path(img_name).name + 'tags' + str(tag_group) + '.txt'
    return app.config['images_tags_dir_path'] / tags_file_name


def flat_all_tags(all_tags):
    res = []
    for tag_group in all_tags:
        if isinstance(tag_group[0], tuple):
            res.append([tag for tag_block in tag_group for tag in tag_block[1]])
        else:
            res.append(tag_group)
    return res


@app.route('/')
def home():
    img_names = get_images_names()
    if img_names:
        is_tag_block = [
            [isinstance(tag_block, tuple) for tag_block in tag_group] for tag_group in app.config['all_tags']
        ]
        return render_template('tag_the_image.html', all_tags=app.config['all_tags'], is_tag_block=is_tag_block)
    else:
        return 'No images! Run the app in the directory containing your images!', 404


@app.route('/metadata')
def metadata():
    initial_img_name = sorted(get_images_names())[0]
    initial_tag_group = 0
    return redirect(url_for('tag_image', img_name=initial_img_name, tag_group=initial_tag_group))


@app.route('/image/<path:img_name>', methods=['GET'])
def image(img_name):
    return send_from_directory(app.config['img_dir_path'], img_name)


@app.route('/tag_image/<path:img_name>', methods=['GET', 'POST'])
def tag_image(img_name, tag_group=0):
    if request.method == 'POST':
        json_data = request.get_json()
        tag_group = json_data['tag_group']
        img_tags_file = get_images_tags_file(img_name, tag_group)
        img_tags_file.open('w').write('\n'.join(json_data['chosen_tags']))
        return Response(status=200)
    else:
        img_tags_file = get_images_tags_file(img_name, tag_group)
        chosen_tags = []
        if img_tags_file.exists():
            chosen_tags = parsers.parse_tags_file(img_tags_file)
        else:
            img_tags_file.touch()

        data = {
            'all_tags': app.config['all_tags_flatten'][tag_group],
            'chosen_tags': chosen_tags,
            'img_name': img_name,
            'tag_group': tag_group,
        }
        return json.dumps(data)


@app.route('/tag_image/previous', methods=['GET'])
def previous():
    params = request.args
    img_names = sorted(get_images_names())
    current_img_name = params['img_name']
    current_img_index = img_names.index(current_img_name)
    current_tag_group = int(params['tag_group'])

    result_img_name = current_img_name
    if current_tag_group % len(app.config['all_tags']) == 0:
        result_img_name = img_names[(current_img_index - 1) % len(img_names)]
    result_tag_group = (current_tag_group - 1) % len(app.config['all_tags'])

    return tag_image(img_name=result_img_name, tag_group=result_tag_group)


@app.route('/tag_image/next', methods=['GET'])
def next():
    params = request.args
    img_names = sorted(get_images_names())
    all_groups_amount = len(app.config['all_tags'])

    current_img_name = params['img_name']
    current_img_index = img_names.index(current_img_name)
    current_tag_group = int(params['tag_group'])

    result_img_name = current_img_name
    if current_tag_group % all_groups_amount == all_groups_amount - 1:
        result_img_name = img_names[(current_img_index + 1) % len(img_names)]
    result_tag_group = (current_tag_group + 1) % all_groups_amount

    return tag_image(img_name=result_img_name, tag_group=result_tag_group)


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
    app.config['all_tags'] = parsers.parse_tags_files(app.config['img_dir_path'])
    app.config['all_tags_flatten'] = flat_all_tags(app.config['all_tags'])
    app.config['images_tags_dir_path'] = app.config['img_dir_path'] / IMAGES_TAGS_DIR
    if not app.config['images_tags_dir_path'].exists():
        app.config['images_tags_dir_path'].mkdir()

    app.run()
