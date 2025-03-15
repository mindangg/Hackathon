import cv2  
import tensorflow as tf  
import numpy as np  

# Load mô hình CNN đã train  
model = tf.keras.models.load_model("pill_classifier.h5")

# Mở webcam  
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Resize ảnh về kích thước phù hợp với model (224x224)
    img = cv2.resize(frame, (224, 224))
    img = np.expand_dims(img, axis=0) / 255.0  

    # Dự đoán
    prediction = model.predict(img)
    print(f"Dự đoán: {np.argmax(prediction)}")  

    cv2.imshow("Webcam", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
