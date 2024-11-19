from geopy.distance import geodesic
import geopandas as gpd
import pandas as pd
import glob
import argparse

# Configuration des arguments de la ligne de commande
parser = argparse.ArgumentParser(description="Filtrer les communes entre deux distances depuis un point central.")
parser.add_argument("min_radius", type=float, help="Distance minimale en kilomètres.")
parser.add_argument("max_radius", type=float, help="Distance maximale en kilomètres.")
args = parser.parse_args()

# Récupération des arguments
min_radius = args.min_radius
max_radius = args.max_radius

# Coordonnées de votre localisation (latitude, longitude)
position = (46.219264, 4.7644672)  # Point fixe défini dans le script

# Liste des fichiers GeoJSON (vous pouvez ajuster le chemin)
geojson_files = glob.glob("./communes-*.geojson")

# Initialiser un GeoDataFrame vide pour stocker toutes les communes
all_communes = gpd.GeoDataFrame()

# Parcourir tous les fichiers et les concaténer dans un seul GeoDataFrame
for file in geojson_files:
    print(f"Lecture du fichier : {file}")
    communes = gpd.read_file(file)
    all_communes = pd.concat([all_communes, communes], ignore_index=True)

# Vérification que des données ont été chargées
if all_communes.empty:
    print("Aucune donnée n'a été chargée à partir des fichiers GeoJSON.")
    exit()

# Affichage des colonnes disponibles pour identifier le code INSEE ou autre information pertinente
print("Colonnes disponibles :", all_communes.columns)

# Reprojection au système de coordonnées projetées (Lambert-93 pour la France)
all_communes = all_communes.to_crs(epsg=2154)

# Calcul des centroides (dans Lambert-93), puis reprojection en WGS84
all_communes['centroid'] = all_communes.geometry.centroid  # Centroid dans CRS projeté
all_communes = all_communes.set_geometry('centroid')  # On passe à la géométrie des centroïdes
all_communes = all_communes.to_crs(epsg=4326)  # Reprojection des centroïdes en WGS84

# Calcul des distances depuis votre position
all_communes['distance'] = all_communes.geometry.apply(
    lambda x: geodesic((x.y, x.x), position).km
)

# Filtrer les communes dans un rayon entre min_radius et max_radius
communes_within_bounds = all_communes[
    (all_communes['distance'] >= min_radius) & (all_communes['distance'] <= max_radius)
]

# Trier les résultats par ordre croissant de distance
communes_within_bounds = communes_within_bounds.sort_values(by="distance")

# Afficher toutes les lignes du DataFrame
pd.set_option('display.max_rows', None)  # Désactiver la limite sur les lignes affichées

# Vérification du résultat
if communes_within_bounds.empty:
    print(f"Aucune commune trouvée entre {min_radius} et {max_radius} km autour de la position {position}.")
else:
    # Utilisation de la colonne 'codeDepartement' pour extraire le numéro de département
    communes_within_bounds['departement'] = communes_within_bounds['codeDepartement'].astype(str).str.zfill(2)
    
    # Ajouter la colonne 'population'
    communes_within_bounds['population'] = communes_within_bounds['population']
    
    # Extraire les informations nécessaires : nom, numéro de département, distance, et population
    output_data = communes_within_bounds[['nom', 'departement', 'distance', 'population']]
    
    # Formater la sortie pour Excel (tabulation séparée ou CSV)
    print("Nom\tDépartement\tDistance (km)\tPopulation")  # Entête pour Excel
    for _, row in output_data.iterrows():
        print(f"{row['nom']}\t{row['departement']}\t{row['distance']:.2f}\t{row['population']}")  # Affichage avec format de distance à 2 décimales

