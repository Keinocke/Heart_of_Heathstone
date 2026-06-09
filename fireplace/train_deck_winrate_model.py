import json
import csv
import xml.etree.ElementTree as ET
from collections import Counter
from xgboost import XGBRegressor
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from lightgbm import LGBMRegressor
from sklearn.neural_network import MLPRegressor

DECKS_JSON_PATH = "generated_decks_FirstEdition.json"
WINRATES_CSV_PATH = "deck_winrates.csv"
CARDDEFS_XML_PATH = r"C:\Users\filip\OneDrive\Dokumenter\Uni\4.år\AppMaschine\FinalProject\fireplace\fireplace\cards\CardDefs_new.xml"


def load_carddefs(path):
    tree = ET.parse(path)
    root = tree.getroot()

    cards = {}

    for entity in root.findall("Entity"):
        card_id = entity.get("CardID")
        if not card_id:
            continue

        card = {
            "name": None,
            "cost": 0,
            "attack": 0,
            "health": 0,
            "cardtype": None,
            "rarity": None,
            "card_class": None,
        }

        for tag in entity.findall("Tag"):
            name = tag.get("name")
            value = tag.get("value")

            if name == "CARDNAME":
                en = tag.find("enUS")
                if en is not None:
                    card["name"] = en.text

            elif name == "COST" and value is not None:
                card["cost"] = int(value)

            elif name == "ATK" and value is not None:
                card["attack"] = int(value)

            elif name == "HEALTH" and value is not None:
                card["health"] = int(value)

            elif name == "CARDTYPE" and value is not None:
                card["cardtype"] = int(value)

            elif name == "RARITY" and value is not None:
                card["rarity"] = int(value)

            elif name == "CLASS" and value is not None:
                card["card_class"] = int(value)

        cards[card_id] = card

    return cards


def load_generated_decks(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    decks = {}

    for class_name, class_decks in raw.items():
        for i, cards in enumerate(class_decks):
            deck_id = f"{class_name}_{i}"
            decks[deck_id] = {
                "class_name": class_name,
                "cards": cards,
            }

    return decks


def load_winrates(path):
    df = pd.read_csv(path)
    return df


def extract_features(deck_id, deck_info, carddefs):
    cards = deck_info["cards"]
    class_name = deck_info["class_name"]

    costs = []
    attacks = []
    healths = []
    cardtypes = []
    rarities = []
    missing_cards = 0

    for card_id in cards:
        card = carddefs.get(card_id)

        if card is None:
            missing_cards += 1
            continue

        costs.append(card["cost"])
        attacks.append(card["attack"])
        healths.append(card["health"])
        cardtypes.append(card["cardtype"])
        rarities.append(card["rarity"])

    type_counts = Counter(cardtypes)
    rarity_counts = Counter(rarities)

    # hearthstone CARDTYPE values in your XML are numeric.
    #4 = minion, 5 = spell, 7 = weapon, 3 = hero.
    features = {
        "deck_id": deck_id,
        "class_name": class_name,
        "avg_cost": sum(costs) / len(costs) if costs else 0,
        "avg_attack": sum(attacks) / len(attacks) if attacks else 0,
        "avg_health": sum(healths) / len(healths) if healths else 0,
        "num_minions": type_counts.get(4, 0),
        "num_spells": type_counts.get(5, 0),
        "num_weapons": type_counts.get(7, 0),
        "num_heroes": type_counts.get(3, 0),
        "num_legendary": rarity_counts.get(5, 0),
        "missing_cards": missing_cards,
    }
    card_counts = Counter(cards)

    for card_id, count in card_counts.items():
        safe_card_id = card_id.replace("-", "_").replace(" ", "_")
        features[f"card_{safe_card_id}"] = count


    return features


def build_dataset():
    carddefs = load_carddefs(CARDDEFS_XML_PATH)
    decks = load_generated_decks(DECKS_JSON_PATH)
    winrates = load_winrates(WINRATES_CSV_PATH)

    rows = []

    for _, row in winrates.iterrows():
        deck_id = row["deck_id"]

        if deck_id not in decks:
            continue

        features = extract_features(deck_id, decks[deck_id], carddefs)
        features["winrate"] = row["winrate"]
        features["wins"] = row["wins"]
        features["losses"] = row["losses"]
        features["draws"] = row["draws"]
        features["games"] = row["games"]

        rows.append(features)

    df = pd.DataFrame(rows)
    df = df.fillna(0)
    return df


def main():
    df = build_dataset()

    print("Dataset shape:", df.shape)
    print(df.head())

    # One-hot encode class names
    df_model = pd.get_dummies(df, columns=["class_name"], drop_first=False)

    y = df_model["winrate"]

    drop_cols = [
        "deck_id",
        "winrate",
        "wins",
        "losses",
        "draws",
        "games",
    ]

    X = df_model.drop(columns=drop_cols)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=73,
    )

    baseline = DummyRegressor(strategy="mean")
    baseline.fit(X_train, y_train)
    baseline_pred = baseline.predict(X_test)

    model = RandomForestRegressor(
        n_estimators=500,
        random_state=73,
        max_depth=None,
        min_samples_leaf=2,
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)


    ridge = make_pipeline(
    StandardScaler(),
    Ridge(alpha=10.0)
)

    ridge.fit(X_train, y_train)
    ridge_pred = ridge.predict(X_test)

    xgb = XGBRegressor(
    n_estimators=300,
    learning_rate=0.03,
    max_depth=3,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=73,
    objective="reg:squarederror",
)

    xgb.fit(X_train, y_train)
    xgb_pred = xgb.predict(X_test)

    

    print("\n===== XGBOOST =====")
    print("MAE:", mean_absolute_error(y_test, xgb_pred))
    print("R2:", r2_score(y_test, xgb_pred))
    xgb_feature_importance = pd.DataFrame({
        "feature": X.columns,
        "importance": xgb.feature_importances_,
    }).sort_values("importance", ascending=False)

    print("\nXGBoost feature importance:")
    print(xgb_feature_importance.head(20))

    xgb_feature_importance.to_csv("xgboost_feature_importance.csv", index=False)


    lgbm = LGBMRegressor(
    n_estimators=300,
    learning_rate=0.03,
    max_depth=3,
    random_state=73,
    verbose=-1,
)

    lgbm.fit(X_train, y_train)
    lgbm_pred = lgbm.predict(X_test)

    nn = make_pipeline(
        StandardScaler(),
        MLPRegressor(
            hidden_layer_sizes=(64, 32),
            activation="relu",
            solver="adam",
            alpha=0.01,
            learning_rate_init=0.001,
            max_iter=2000,
            random_state=42,
            early_stopping=True,
        )
    )

    nn.fit(X_train, y_train)
    nn_pred = nn.predict(X_test)

    print("\n===== NEURAL NETWORK =====")
    print("MAE:", mean_absolute_error(y_test, nn_pred))
    print("R2:", r2_score(y_test, nn_pred))



    print("\n===== LIGHTGBM =====")
    print("MAE:", mean_absolute_error(y_test, lgbm_pred))
    print("R2:", r2_score(y_test, lgbm_pred))





    print("\n===== RIDGE REGRESSION =====")
    print("MAE:", mean_absolute_error(y_test, ridge_pred))
    print("R2:", r2_score(y_test, ridge_pred))

    print("\n===== BASELINE =====")
    print("MAE:", mean_absolute_error(y_test, baseline_pred))
    print("R2:", r2_score(y_test, baseline_pred))

    print("\n===== RANDOM FOREST =====")
    print("MAE:", mean_absolute_error(y_test, pred))
    print("R2:", r2_score(y_test, pred))

    results = pd.DataFrame({
        "true_winrate": y_test.values,
        "predicted_winrate": xgb_pred,
    })

    print("\nPredictions:")
    print(results.head(20))

    feature_importance = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)

    print("\nFeature importance Random forest:")
    print(feature_importance.head(20))

    df.to_csv("deck_ml_dataset.csv", index=False)
    results.to_csv("deck_winrate_predictions.csv", index=False)
    feature_importance.to_csv("feature_importance.csv", index=False)

    print("\nSaved:")
    print("deck_ml_dataset.csv")
    print("deck_winrate_predictions.csv")
    print("feature_importance.csv")


if __name__ == "__main__":
    main()