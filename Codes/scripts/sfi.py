import os
import sys
os.chdir('./')
sys.path.append('./')
import re
from utils.utils import evaluate,train,prepare,load_hparams,test,tune,load,encode

if __name__ == "__main__":

    hparams = {
        'name':'sfi',
        'dropout_p':0.2,
        'embedding_dim':300,
        'filter_num':150,
    }
    hparams = load_hparams(hparams)

    if hparams['mode'] == 'encode':
        vocab, loaders = prepare(hparams, news=True)
    else:
        vocab, loaders = prepare(hparams)

    if hparams['encoder'] == 'fim':
        from models.Encoders.FIM import FIM_Encoder
        encoder = FIM_Encoder(hparams, vocab)

    elif hparams['encoder'] == 'mha':
        hparams['value_dim'] = 16
        hparams['query_dim'] = 200
        hparams['head_num'] = 16
        from models.Encoders.MHA import MHA_Encoder
        encoder = MHA_Encoder(hparams, vocab)

    elif hparams['encoder'] == 'npa':
        hparams['user_dim'] = 200
        hparams['query_dim'] = 200
        hparams['filter_num'] = 400
        from models.Encoders.NPA import NPA_Encoder
        encoder = NPA_Encoder(hparams, vocab, len(loaders[0].dataset.uid2index))

    elif hparams['encoder'] == 'nrms':
        hparams['value_dim'] = 16
        hparams['query_dim'] = 200
        hparams['head_num'] = 16
        from models.Encoders.MHA import NRMS_Encoder
        encoder = NRMS_Encoder(hparams, vocab)

    elif hparams['encoder'] == 'cnn':
        from models.Encoders.General import CNN_Encoder
        encoder = CNN_Encoder(hparams, vocab)

    elif hparams['encoder'] == 'pipeline':
        from models.Encoders.General import Pipeline_Encoder
        encoder = Pipeline_Encoder(hparams)

    elif hparams['encoder'] == 'bert':
        hparams['encoder'] = hparams['encoder'] + '-[{}]'.format(hparams['bert'])
        from models.Encoders.General import Bert_Encoder
        encoder = Bert_Encoder(hparams)

    else:
        raise ValueError("Undefined Encoder:{}".format(hparams['encoder']))

    if hparams['interactor'] == 'fim':
        from models.Interactors.FIM import FIM_Interactor
        interactor = FIM_Interactor(encoder.level)

    elif hparams['interactor'] == 'knrm':
        from models.Interactors.KNRM import KNRM_Interactor
        interactor = KNRM_Interactor()

    elif hparams['interactor'] == '2dcnn':
        from models.Interactors.CNN import CNN_Interator
        interactor = CNN_Interator(hparams['k'])

    elif hparams['interactor'] == 'mha':
        from models.Interactors.MHA import MHA_Interactor
        interactor = MHA_Interactor(encoder.hidden_dim)

    else:
        raise ValueError("Undefined Interactor:{}".format(hparams['interactor']))

    # FIXME, treat encode as a argument, encode=train means only encode training dataset
    if hparams['mode'] == 'encode':
        from models.Encoders.General import Encoder_Wrapper
        hparams['name'] = '-'.join([i for i in [hparams['name'], hparams['encoder'], hparams['interactor'], hparams['coarse']] if i])
        encoder_wrapper = Encoder_Wrapper(hparams, encoder).to('cpu').eval()

        load(encoder_wrapper, hparams, hparams['epochs'], hparams['save_step'][0])
        encode(encoder_wrapper, hparams, loader=loaders[1])
        # pipeline_encode(encoder_wrapper, hparams, loaders)

    if hparams['multiview']:
        hparams['name'] = 'sfi-multiview'
        if hparams['coarse']:
            from models.SFI import SFI_unified_MultiView
            sfiModel = SFI_unified_MultiView(hparams, encoder, interactor).to(hparams['device'])

        else:
            from models.SFI import SFI_MultiView
            sfiModel = SFI_MultiView(hparams, encoder, interactor).to(hparams['device'])

    else:
        if hparams['coarse']:
            from models.SFI import SFI_unified
            sfiModel = SFI_unified(hparams, encoder, interactor).to(hparams['device'])

        else:
            from models.SFI import SFI
            sfiModel = SFI(hparams, encoder, interactor).to(hparams['device'])

    if re.search('pipeline', sfiModel.encoder.name):
        hparams['name'] = hparams['pipeline']
    else:
        hparams['name'] = '-'.join([i for i in [hparams['name'], hparams['encoder'], hparams['interactor'], hparams['coarse']] if i])

    if hparams['mode'] == 'dev':
        evaluate(sfiModel,hparams,loaders[0],loading=True)

    elif hparams['mode'] == 'train':
        train(sfiModel, hparams, loaders)

    elif hparams['mode'] == 'tune':
        tune(sfiModel, hparams, loaders)

    elif hparams['mode'] == 'test':
        # from models.Encoders.General import Encoder_Wrapper,Pipeline_Encoder

        # device = hparams['device']

        # if not 'multiview' in hparams:
        #     hparams['device'] = 'cpu'
        #     encoder_wrapper = Encoder_Wrapper(hparams, encoder.to('cpu'))
        #     load(encoder_wrapper, hparams, hparams['epochs'], hparams['save_step'][0])
        #     encode(encoder_wrapper, hparams)

        #     hparams['device'] = device
        #     hparams['pipeline'] = 'sfi-fim-fim-gating'
        #     encoder = Pipeline_Encoder(hparams)
        #     sfiModel = SFI_gating(hparams, encoder).to(hparams['device'])
        #     test(sfiModel, hparams, loaders[0])

        # else:
        test(sfiModel, hparams, loaders[0])