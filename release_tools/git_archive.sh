if [ ! -f simstack ]
then
    echo "Main executable not found, quitting."
    exit 0
fi
git archive --format zip --output nanomatch-client.zip develop
cd external/pyura 
git archive --prefix external/pyura/ --format zip --output ../../pyura_archive.zip dev
cd -

mkdir nanomatch-client
cd nanomatch-client
unzip ../nanomatch-client.zip
unzip ../pyura_archive.zip
cd -
rm nanomatch-client.zip pyura_archive.zip

zip -r nanomatch-client.zip nanomatch-client
rm -r nanomatch-client
