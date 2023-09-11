[FR]
Le plugin videojs-hlsjs-plugin a été compilé et est fourni avec le code source pour être compatible avec la version 1.3 de la lib hls.js. 
Une issue est créée avec la PR correspondante. Voici le lien : https://github.com/streamroot/videojs-hlsjs-plugin/issues/116
Pour compiler le plugin, voici les commandes lancées :
[EN]
The videojs-hlsjs-plugin has been compiled and comes with the source code to be compatible with version 1.3 of the hls.js lib.
An issue is created with the corresponding PR. Here is the link: https://github.com/streamroot/videojs-hlsjs-plugin/issues/116
To compile the plugin, here are the commands launched:

> git clone https://github.com/ptitloup/videojs-hlsjs-plugin.git
> cd videojs-hlsjs-plugin/
> git checkout ptitloup-patch-bump-hls.js
> export NODE_OPTIONS=--openssl-legacy-provider
> npm install
> npm run build
