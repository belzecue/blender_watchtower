const paletteDefault = [
  [0.8197601437568665, 0.7117544412612915, 0.5497459173202515, 1.0],
  [0.6462640762329102, 0.5692625641822815, 0.8191020488739014, 1.0],
  [0.5096713304519653, 0.7521656155586243, 0.5136501789093018, 1.0],
  [0.8272907137870789, 0.5883985161781311, 0.6541866064071655, 1.0],
  [0.5273313522338867, 0.6598359346389770, 0.7609495520591736, 1.0],
  [0.7392144799232483, 0.7697654366493225, 0.5531221032142639, 1.0],
  [0.7357943654060364, 0.5509396195411682, 0.7686146497726440, 1.0],
  [0.5617250204086304, 0.7625861167907715, 0.6736904978752136, 1.0],
  [0.8007439970970154, 0.6388462185859680, 0.5802854895591736, 1.0],
  [0.6019799709320068, 0.6073563694953918, 0.8074616789817810, 1.0],
  [0.5944148898124695, 0.7527848482131958, 0.5205842256546020, 1.0],
  [0.8126696348190308, 0.5513396859169006, 0.7106873989105225, 1.0],
  [0.5918391346931458, 0.7710464000701904, 0.7906153798103333, 1.0],
  [0.7648254632949829, 0.7191355228424072, 0.5285170674324036, 1.0],
  [0.6757139563560486, 0.5736276507377625, 0.7719092965126038, 1.0],
  [0.5477100014686584, 0.7845347523689270, 0.6005358695983887, 1.0],
  [0.7501454353332520, 0.5404607057571411, 0.5548738241195679, 1.0],
  [0.5506091117858887, 0.6321061849594116, 0.7766551971435547, 1.0],
  [0.7142684459686279, 0.7983494400978088, 0.5565086007118225, 1.0],
  [0.6019799709320068, 0.5404607057571411, 0.7686146497726440, 1.0],
  [0.5555555555555555, 0.5555555555555555, 0.5555555555555555, 1.0],
]

export default {
  paletteDefault,
  hexToRGB (hex) {
  let r = parseInt(hex.slice(1, 3), 16) / 255,
      g = parseInt(hex.slice(3, 5), 16) / 255,
      b = parseInt(hex.slice(5, 7), 16) / 255;
  return [r, g, b, 1.0]
  },
  batchConvertColorHexToRGB (items) {
    /* Given a list of objects, convert the object attribute to RGB */
    for (let i = 0; i < items.length; i++) {
      let item = items[i];
      item.color = this.hexToRGB(item.color);
    }
  },
  batchAssignColor (items) {
    /* Given a list of objects, assign a sequential color from the default palette */
    let colorPaletteIndex = 0;
    for (let i = 0; i < items.length; i++) {
      let item = items[i];
      item.color = this.paletteDefault[colorPaletteIndex];
      // Loop through the color palette if we reach the end
      // We use +2 to skip the last color of the palette (Grey)
      // as it's used for 'disabled' or 'unassigned' states
      if (colorPaletteIndex + 2 < this.paletteDefault.length) {
        colorPaletteIndex++;
      } else {
        colorPaletteIndex = 0;
      }
    }
  }
}
