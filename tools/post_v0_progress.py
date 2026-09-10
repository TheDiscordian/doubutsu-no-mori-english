"""Bind completed post-v0 cartridges before checking their unchanged base text.

The older letter adapters verify an entire reconstructed cartridge. These exact
ROM/report pairs retain that base while adding independently checked corrections
and artwork. Unknown newer builds must be reviewed and registered, not silently
accepted. The counter still verifies current installed routes against the current
ROM; this predecessor is used only for the old whole-cartridge letter chain.
"""
import json
from pathlib import Path

from aflib import sha256

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '31c85f23c996b70bd7a4779b43f1039716a77c84806dfa5a7dd52e3780d50860'
APPROVED = {
    '69c695c746959f9c3f5b2bda3d56020ce24fdd7a1ec341285ea9696f0738c7c4': '62feafa0cb9780f5af1d16993464a16ea0618a40cbe5aded6f4bc8d0a209043f',
    'ec2917b38e47e936b69b203ffa99913e7fedad9d4ae29e8c368db5441b64ed13': '0bc1494cb8d999ac0fe007f57afa44d56a2bdb6547db0c939c7a70286eb72da5',
    '5c5206c9a8ee548900ba264276f5052a4ed8b5a13803ffcf1a6b44c880f17226': '04c0c92d489c3fe8524769a872772942f721e4a6169294cbcd0fbb5aa41b9194',
    '2795a31a259996395dafb5df4e46c00f46a1109eda46e6a15119927d9d01d193': '4d4f45e5a50d16bb689ad556fbfbc51e96301b9e40136717a1f4870279b632d1',
    '0173bb83decfda63b299fb40aedd22121b546818081754032e60fc3b96d9a257': 'f781bd9dc8e2dccbdd8c3125e9f0e9fe8c080c0c6daec5368761b2159fcf2bd5',
    '9f12c83314b048225e87c0c4ba46853caf3dadb21f863a234ca03a879987474d': 'c818eb98fea0e63d99c655bfed9db8b7337e076297a1e7efec601712531ebc14',
    'e6511dfe0a51b75f8764eeed0159a31ee651f6d650075f42501977b0ea1d8483': '60d2e11b0df8047c8be0e7264a7a30f2794d822e6c767f343aa76eb19137b467',
    '179c658a70383d278b2b78aa9f2d339c8582ae2cb714e7b95b120163c0104d5d': '679118f92785acab6f48fdb5304154fdac5f3daa3640f120f095a12ba3f580f4',
    '23f9d9724827d0de3c91bd00a91349b04b0d45371d1930ef71cdbb95910e711e': 'ac1a83ca2f63c8881bc792c6e71489837a071eb40ca8185065b49bba525b3322',
    '67f72b69017452be3ec83e05a513502fd58752bd0cf96b000a182fee4f880a58': '5cd20da84a8ceef4bd7d6bfad4e8dd71f30e17139c27d9d30342ac4de599d539',
    '4fcebd1758f3ca5bed1a9c7dd3659f961f27d51572ea5b4f13c49039e2b8d963': '69c324ab79c270414ce3b5a94d94aa7ca02b0c6fab43241d09055fd5e5f0c450',
    '96d2b253bdf727bf537c416d49fdd0a0eb70abfe0be8a0c8ade9dafbd46de941': 'be4105088062051fc1daba3cfde5821d042ed68995f472e1acea23d08b020ddc',
    '2725492f603d6dda9d1984ae4e3dcced520786a6c43e9180082e288d62cdd419': '544d460f2002d7d7dd78f896f504d0b0f68625a52cd59ab75162ade69ef5e3f7',
    '6c44e1d71b7d3d13864c576138ad983a4c9747a1bf2e97d268fc576ba3fa8811': '49e6980d0c4a4e4dddbd0a223ce49b122eae69cef1c65e783aca37054197f4ff',
    '90c1280d768132a07002bcf44ceefa1f8f872606f3ac186e069af64f5db38980': '178ec07de694e4b91b3d8a2b185f0d7bfc8214d5dcfc60336bec606b07aa55d7',
    'b93a54b8804f262e1c05e7dabcd6aac4f5b47d637c69d94264f058c12dbdbd35': '5fe4d9b4731470dd9f095f88165133fc629622d6478d9e0b6dd86e65742606a0',
    '507ddfe5ed585bcd6e20fbab44f7247315339a9c90b66dacec03b1e6b22fbc3a': '62b08e3c3bf2cde09d120cbcaf64f8030f9e40da99d7a141d5cb600a77cd348e',
    '29576ea8bc82a55193a263b913a15ffe81554746a2cec5cdcff3bf84a26b6cdc': 'f8052b03a10f6bf838f446c8bd151e66384bff39b06fe08bc50c2bc3ef99fabf',
    '15c7a2830f5a561a8470ba70bc4aaa907e65ab1ee5ebb921266df17e6b1cac3c': '8513cc8f5d4ace7f88983546bf7758e7b86b36fa5f004e81e9fe1621e9f3a96a',
    '54a6d643d27cd36345e2298407f47f5bb51ddf2c6f947558391da968cbf717be': 'e54613d9ebcde3921bf4898a2c80d133b1d233d87da4ba2391ff7eba814fa640',
    '27f840aaea2693ac96fbbc084981dd978f8e376cbf8d7a1259666160d29f5f7d': '358a7ef4e492c258d86477bdc95ba77542b729574439f7fc9642a164df590c65',
    'e5f2a22f50f89fdf7e0e9743368abf9a2f4d261e303dc0339f5cbbc4a0ad48f7': '57033d949a542b192d0fb5008fa0c23a42cdd4d76a9ad024e27fe1484e5dd723',
    '28c551708dbbc1d78333abc7ebf81d5001663859775ca9f85427ced8208b0020': 'f57d2fde252ccd2e9ca90149437786cd28c13ae199bc3433ac9da1cd8075b45d',
    '58e02d5ccc8807ce6adffbcfa20502a10df0f7b2639147956ae1a14e3ca3de74': 'e846c0c7a73c908a212ce5773d489a78aed3da6c5fb385cd6c76ef5a171c8a35',
    '7ec5ba6eb5a68e15a3c89ab37111cf758a5b02241a1f51291cebf174b64ef6ad': '02c4070a53f11730268a87dc7fc09c9e026d06a9d395c57d968b0fe37c028a6d',
    '7cba9ed279dd90b8fa903cd3ab1745aacf7bd0383c5b43347cadc1bf6fecc39a': '9fab405c72fcc22124b87600ff5332ee0aef8cac35e0b6cb6c7ba169fe827ff2',
}


def predecessor(built, report):
    digest = sha256(built)
    if digest not in APPROVED or sha256(json.dumps(report, sort_keys=True, separators=(',', ':')).encode()) != APPROVED[digest]:
        raise ValueError('Post-v0 progress requires an approved complete cartridge/report pair')
    directory = ROOT/'build/classic-letters-pilot'
    base = (directory/'animal-forest-halfwidth.z64').read_bytes()
    previous = json.loads((directory/'build.json').read_text())
    if sha256(base) != BASE_SHA or previous.get('output_sha256') != BASE_SHA:
        raise ValueError('Changed post-v0 text predecessor')
    # The caller runs the existing strict classic-letter verifier on both parts.
    return base, previous
