import os
import glob
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from model import improv_unet

# constants
BATCH = 7
CHANNEL_NUM = 3
LEARN_RATE = 0.00004
TEST_RATIO = 0.3
SAMPLING_SIZE = 100


def convert_png(f):
    """
    convert png into images for the model
    Args:
        f: list of images

    Returns: images for model

    """
    seg = tf.io.read_file(f)
    seg = tf.image.decode_png(seg, channels=1)  # gray scale
    seg = tf.image.resize(seg, (256, 256))
    seg = tf.cast(seg, tf.float32) / 255.0  # need to divide
    seg = tf.math.round(seg)  # round so that it is binary
    return seg


def process_images(image_path, mask_path):
    """
    process source into images for model
    Args:
        image_path:  path for images
        mask_path:  path for masks

    Returns: list of images

    """
    image = tf.io.read_file(image_path)
    image = tf.image.decode_jpeg(image, channels=1)
    image = tf.image.resize(image, (256, 256))
    image = tf.cast(image, tf.float32) / 255.0
    segmentation = convert_png(mask_path)

    # reshape them both to be 256, 256, 1
    image = tf.reshape(image, (256, 256, 1))
    segmentation = tf.reshape(segmentation, (256, 256, 1))
    return image, segmentation


def dice_coefficient(x, y):
    """
    Returns:
        int: dice coefficient
    """
    return 2 * (tf.keras.backend.sum(tf.keras.backend.flatten(x) * tf.keras.backend.flatten(y)) + 1) / \
           (tf.keras.backend.sum(tf.keras.backend.flatten(x) + tf.keras.backend.flatten(y)) + 1)


def dice_loss(x, y):
    """
    Returns:
        int:  dice co-efficient loss
    """
    return 1 - dice_coefficient(x, y)


def return_model_results():
    """
    compile train and evaluate the model
    Returns: result of the model

    """
    # download pictures
    tf.keras.utils.\
        get_file(origin="https://cloudstor.aarnet.edu.au/sender/?s=download&token=723595dd-15b0-4d1e-87b8-237a7fe282ff",
                 fname=os.getcwd() + '\ISIC2018_Task1-2_Training_Data.zip', extract=True, cache_dir=os.getcwd())
    x_images = sorted(glob.glob('datasets/ISIC2018_Task1-2_Training_Input_x2/*.jpg'))[:SAMPLING_SIZE]
    mask_images = sorted(glob.glob('datasets/ISIC2018_Task1_Training_GroundTruth_x2/*.png'))[:SAMPLING_SIZE]
    # split the images into training, testing and validation
    x_train, x_test, y_train, y_test = train_test_split(x_images, mask_images, test_size=TEST_RATIO)
    x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, test_size=TEST_RATIO)

    # Put the images into a data set from a list
    train_data = tf.data.Dataset.from_tensor_slices((x_train, y_train))
    test_data = tf.data.Dataset.from_tensor_slices((x_test, y_test))
    val_data = tf.data.Dataset.from_tensor_slices((x_val, y_val))

    # shuffle the images
    train_set = train_data.shuffle(len(x_train))
    test_set = test_data.shuffle(len(x_test))
    validation_set = val_data.shuffle(len(x_val))

    # put the images into a map
    train_set = train_set.map(process_images)
    test_set = test_set.map(process_images)
    validation_set = validation_set.map(process_images)

    model = improv_unet()
    model.compile(tf.keras.optimizers.Adam(lr=LEARN_RATE), metrics=[dice_coefficient, 'accuracy'], loss=dice_loss)
    model.summary()
    hist = model.fit(train_set.batch(BATCH), epochs=10, validation_data=validation_set.batch(BATCH))
    eval = model.evaluate(test_set.batch(BATCH))
    return hist, eval


hist, eval = return_model_results(SAMPLING_SIZE)

fig, axs = matplotlib.plt.subplots(3)
fig.tight_layout()
fig.legend(loc='right')
fig.set_size_inches(16, 16)

y_label = ["accuracy", "loss", "dice coefficient"]
for i in range(3):
    axs[i].set_xlabel("Epochs")
    axs[i].set_ylabel(y_label[i])

axs[0].plot(hist.history['accuracy'], label='training accuracy', color="r")
axs[0].plot(hist.history['val_accuracy'], label='validation accuracy', color="y")

axs[1].plot(hist.history['loss'], label='training loss', color='g')
axs[1].plot(hist.history['val_loss'], label='validation loss', color='c')

axs[2].plot(hist.history['dice_coefficient'], label='training dice coefficient', color='b')
axs[2].plot(hist.history['val_dice_coefficient'], label='validation dice coefficient', color='m')
matplotlib.plt.show()


# shows predictions of model
print("Predictions")
matplotlib.plt.figure(figsize=(4 * 4, 3 * 4))
i = 0
for image, mask in final_test.take(3):
    predictions = model.predict(image[tf.newaxis, ...])[0]
    matplotlib.plt.subplot(3, 4, 4 * i + 1)
    matplotlib.plt.imshow(image)
    matplotlib.plt.subplot(3, 4, 4 * i + 2)
    matplotlib.plt.imshow(mask[:, :, 0], cmap='gray')
    matplotlib.plt.subplot(3, 4, 4 * i + 3)
    matplotlib.plt.imshow(predictions[:, :, 0], cmap='gray')
    i = i + 1
matplotlib.plt.show()
