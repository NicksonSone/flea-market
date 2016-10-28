import cStringIO
from PIL import Image

@app.route("/image/upload", methods=["POST", "OPTIONS"])
@allow_cross_domain
def image_upload():
    if request.method == 'POST':
        image = request.files['fileList']
        if image:
            bucket = Bucket("avatar")
            numObejcts = int(bucket.stat()["objects"])
            imageId = str(numObejcts + 1) + ".jpg"

            # use Image to process
            outbuf = cStringIO.StringIO()
            size = (800, 900)
            process = Image.open(image.stream)
            process.resize(size, Image.BILINEAR)
            process.save(outbuf, "JPEG")

            bucket.put_object(imageId, outbuf)
            # bucket.put_object(imageId, image.stream)
            url = bucket.generate_url(imageId)

            return url
    return jsonify(error="fail to upload image")
