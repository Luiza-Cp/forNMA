import cv2 as cv
import os


# Function which will be called on mouse input
def drawRectangle(action, x, y, flags, param):
    if action == cv.EVENT_LBUTTONDOWN:
        image, temp = param
        # Clear the previous drawing
        image[:] = temp.copy()
        # Mark the new position
        cell = (x, y)
        cv.putText(image, 'x', cell, cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv.imshow("Window", image)


def function(value, image_list, temp_list):
    value = cv.getTrackbarPos('Image', "Window")
    image = image_list[value]
    temp = temp_list[value]
    cv.imshow('Window', image)
    cv.setMouseCallback("Window", drawRectangle, (image, temp))

# Read Images
path = '/media/luiza/DATA/Doutorado/forNMA/experimentos/exp_kaka/Experimento_Karine-Julia_STV+TMZ_100_uM/results/results geral/A1_2/frames0-20'

image_names = sorted(os.listdir(path))
image_paths = [os.path.join(path, i) for i in image_names]
images = [cv.imread(i) for i in image_paths]
temps = [img.copy() for img in images]  # Make copies of the images

# Create a named window
cv.namedWindow("Window", cv.WINDOW_NORMAL)
cv.createTrackbar('Image', 'Window', 0, len(images)-1, lambda value: function(value, images, temps))

# Display the first image
cv.imshow("Window", images[0])

# Main loop
k = 0
while k != 113:  # 113 is the ASCII code for 'q'
    k = cv.waitKey(0)
    # If 'c' is pressed, clear the window by restoring the original image
    if k == 99:  # 99 is the ASCII code for 'c'
        value = cv.getTrackbarPos('Image', "Window")
        images[value] = temps[value].copy()
        cv.imshow("Window", images[value])

cv.destroyAllWindows()