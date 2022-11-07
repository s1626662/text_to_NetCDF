# Filename: 'boundary_tester.py'
# Date: 07/11/2022
# Author: Connor Jordan
# Institution: University of Edinburgh (IIE)
# This script takes x, y, z data and tries to determine the boundary using alpha shapes.
# https://stackoverflow.com/questions/72418933/find-boundary-points-of-xy-coordinates
# https://stackoverflow.com/questions/50549128/boundary-enclosing-a-given-set-of-points
# https://gist.github.com/AndreLester/589ea1eddd3a28d00f3d7e47bd9f28fb

from datetime import datetime
import matplotlib.pyplot as plt
import alphashape
import numpy as np
import shapely.geometry as geometry
from shapely.ops import cascaded_union, polygonize
from scipy.spatial import Delaunay, ConvexHull, convex_hull_plot_2d
import fiona
from sys import exit

test = True

# Step 1: Load in data

starttime = datetime.now()  # calculating run times

print('Modules imported... (', datetime.now() - starttime, ')')

dt_string = starttime.strftime("%d/%m/%Y %H:%M:%S")
print("Simulation start: ", dt_string, '\n')

if test is True:
    data = np.loadtxt('tester.txt', delimiter=",", skiprows=1)
else:
    data = np.load('../bathymetry.npy')

print('Bathymetry data loaded... (', datetime.now() - starttime, ')')

Coords = data[:, :-1]  # remove final column i.e. elevation data

x, y = Coords[:, 0], Coords[:, 1]



# Option 1 - alphashapes

t1 = datetime.now()
Boundary = alphashape.alphashape(Coords, alpha=1.0)
print('Boundary generated... (', datetime.now() - starttime, ')')

print(Boundary)

Boundary_x, Boundary_y = Boundary.exterior.coords.xy
print('Boundary coordinates split... (', datetime.now() - starttime, ')')

Boundaries = np.asarray([Boundary_x, Boundary_y]).T

t2 = datetime.now()

# plt.plot(x, y, 'o', color='black', markersize=6)
plt.plot(Boundaries[:, 0], Boundaries[:, 1], 'x', color='red', markersize=4)

plt.show()




# Option 2 - alpha_shapes (custom)

t3 = datetime.now()
def alpha_shape(points, alpha):
    """
    Compute the alpha shape (concave hull) of a set
    of points.
    @param points: Iterable container of points.
    @param alpha: alpha value to influence the
        gooeyness of the border. Smaller numbers
        don't fall inward as much as larger numbers.
        Too large, and you lose everything!
    """
    if len(points) < 4:
        # When you have a triangle, there is no sense
        # in computing an alpha shape.
        return geometry.MultiPoint(list(points)).convex_hull

    # coords = np.array([point.coords[0] for point in points])
    # tri = Delaunay(coords)
    tri = Delaunay(points)
    triangles = points[tri.vertices]
    a = ((triangles[:, 0, 0] - triangles[:, 1, 0]) ** 2 + (triangles[:, 0, 1] - triangles[:, 1, 1]) ** 2) ** 0.5
    b = ((triangles[:, 1, 0] - triangles[:, 2, 0]) ** 2 + (triangles[:, 1, 1] - triangles[:, 2, 1]) ** 2) ** 0.5
    c = ((triangles[:, 2, 0] - triangles[:, 0, 0]) ** 2 + (triangles[:, 2, 1] - triangles[:, 0, 1]) ** 2) ** 0.5
    s = ( a + b + c ) / 2.0
    areas = (s*(s-a)*(s-b)*(s-c)) ** 0.5
    circums = a * b * c / (4.0 * areas)
    filtered = triangles[circums < (1.0 / alpha)]
    edge1 = filtered[:, (0, 1)]
    edge2 = filtered[:, (1, 2)]
    edge3 = filtered[:, (2, 0)]
    edge_points = np.unique(np.concatenate((edge1, edge2, edge3)), axis = 0).tolist()
    m = geometry.MultiLineString(edge_points)
    triangles = list(polygonize(m))
    return cascaded_union(triangles), edge_points

Boundary, edgepoints = alpha_shape(Coords, alpha=1)
print('v2_Boundary generated... (', datetime.now() - starttime, ')')

Boundary_x, Boundary_y = Boundary.exterior.coords.xy
print('Boundary coordinates split... (', datetime.now() - starttime, ')')

Boundaries = np.asarray([Boundary_x, Boundary_y]).T
t4 = datetime.now()
# plt.plot(x, y, 'o', color='black', markersize=6)
plt.plot(Boundaries[:, 0], Boundaries[:, 1], 'x', color='red', markersize=4)

plt.show()

# Define a polygon feature geometry with one attribute
schema = {
    'geometry': 'Polygon',
    'properties': {'id': 'int'},
}

# Write a new Shapefile
with fiona.open('boundary.shp', 'w', 'ESRI Shapefile', schema, crs='epsg:32630') as output:
    output.write({'geometry': geometry.mapping(Boundary), 'properties': {'id': 0}})




# hull = ConvexHull(Coords)
# for simplex in hull.simplices:
#     plt.plot(Coords[simplex, 0], Coords[simplex, 1], 'k-')
#
# plt.show()
#
# print(hull)

print('alphashapes, full data:', t2-t1, 's')

print('alpha_shapes, full data:', t4-t3, 's')

exit(0)