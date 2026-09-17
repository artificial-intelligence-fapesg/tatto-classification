from tensorflow.keras.regularizers import l2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (Rescaling,Conv2D,MaxPooling2D,Flatten,Dense,Dropout,GlobalAveragePooling2D,RandomFlip,RandomRotation,RandomContrast)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.metrics import (confusion_matrix,ConfusionMatrixDisplay,classification_report)
from tensorflow.keras.applications import ConvNeXtBase

def build_model():
    model = Sequential([
        Rescaling(1.0 / 255,input_shape=(224, 224, 3)),

        # Data Augumentation
        RandomFlip("horizontal_and_vertical"),
        RandomRotation(0.2),
        RandomContrast(0.2),

        # Camada Convolucional
        Conv2D(32,kernel_size=(3, 3),activation="relu", padding="same"),
        MaxPooling2D(pool_size=(2, 2)),
        Conv2D(64,kernel_size=(3, 3),activation="relu", padding="same"),
        MaxPooling2D(pool_size=(2, 2)),
        Conv2D(128,kernel_size=(3, 3),activation="relu", padding="same"),
        MaxPooling2D(pool_size=(2, 2)),

        Flatten(),
        Dropout(0.4),

        # Funil de camadas
        Dense(512,activation="relu", kernel_regularizer=l2(1e-4)),
        Dropout(0.5),
        Dense(256,activation="relu", kernel_regularizer=l2(1e-4)),
        Dropout(0.5),
        Dense(6,activation="softmax")
        ])

    return model