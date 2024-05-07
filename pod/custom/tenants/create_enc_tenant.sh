#!/bin/bash
## Variable à définir
NAME=$2
ID_SITE=$1
DOMAIN_NAME=$3

echo "Script executed from: ${PWD}"

BASEDIR=${PWD}

echo "remove previous site"
rm -rf "./$NAME"
sudo rm -f "/etc/init.d/celeryd_$NAME"
sudo rm -f "/etc/default/celeryd_$NAME"

echo "Creation du site numéro $ID_SITE ayant pour identifiant $NAME et pour domaine $DOMAIN_NAME"
echo "Creation du répertoire"
cp -r ./source_enc "./$NAME"

echo "Fichier de configuration"
mv "./$NAME/tenant_enc_settings.py" ./$NAME/"$NAME"_enc_settings.py
sed -i "s/__NAME__/$NAME/g" ./$NAME/"$NAME"_enc_settings.py
sed -i "s/__ID_SITE__/$ID_SITE/g" ./$NAME/"$NAME"_enc_settings.py
sed -i "s/__DOMAIN_NAME__/$DOMAIN_NAME/g" ./$NAME/"$NAME"_enc_settings.py

echo "Fichier de lancement Celery"
sudo cp /etc/init.d/celeryd "/etc/init.d/celeryd_$NAME"
mv "./$NAME/celeryd-tenant" "./$NAME/celeryd_$NAME"
sed -i "s/__NAME__/$NAME/g" "./$NAME/celeryd_$NAME"
sed -i "s/__ID_SITE__/$ID_SITE/g" "./$NAME/celeryd_$NAME"
sed -i "s/__DOMAIN_NAME__/$DOMAIN_NAME/g" "./$NAME/celeryd_$NAME"
#sudo ln -s $BASEDIR/$NAME/celeryd_$NAME /etc/default/celeryd_$NAME
sudo cp "$BASEDIR/$NAME/celeryd_$NAME" "/etc/default/celeryd_$NAME"
sudo chmod 640 "/etc/default/celeryd_$NAME"

echo "fichier de configuration Celery"
sed -i "s/__NAME__/$NAME/g" "./$NAME/celery.py"
sed -i "s/__ID_SITE__/$ID_SITE/g" "./$NAME/celery.py"
sed -i "s/__DOMAIN_NAME__/$DOMAIN_NAME/g" "./$NAME/celery.py"

echo "__FIN__"
echo "Pour lancer le woker, il suffit de lancer cette commande :"
echo "$> sudo /etc/init.d/celeryd_$NAME start"
