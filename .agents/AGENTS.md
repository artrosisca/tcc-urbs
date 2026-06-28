# URBS Process Mining Dashboard Rules

## Deck.gl v9 TileLayer Rendering
When using `TileLayer` from `@deck.gl/geo-layers` in deck.gl v9 to render raster tiles (such as CartoDB or OpenStreetMap), always remember that `TileLayer` is a `CompositeLayer` and does not render anything directly.
You must:
1. Import `BitmapLayer` from `@deck.gl/layers`.
2. Define the `renderSubLayers` property on the `TileLayer` to instantiate and return a `BitmapLayer` mapping the tile's bounding box (`bbox` property of `props.tile` which has `{ west, south, east, north }`).

Example:
```javascript
import { TileLayer } from '@deck.gl/geo-layers';
import { BitmapLayer } from '@deck.gl/layers';

new TileLayer({
  id: 'base-tiles',
  data: 'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
  minZoom: 0,
  maxZoom: 19,
  tileSize: 256,
  renderSubLayers: props => {
    const { bbox } = props.tile;
    if (!bbox) return null;
    const { west, south, east, north } = bbox;
    return new BitmapLayer(props, {
      data: null,
      image: props.data,
      bounds: [west, south, east, north]
    });
  }
})
```
