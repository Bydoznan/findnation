'use client';

import ReportFormInput from '@/components/ReportFormInput';

const ReportForm = () => {
  return (
    <section className='flex w-200 flex-col items-center justify-start bg-white p-10 shadow-xl'>
      <h1 className='my-8 text-2xl font-bold text-neutral-600'>
        FORMULARZ ZGŁOSZENIOWY
      </h1>
      <div className='flex flex-col items-start justify-center gap-4'>
        <ReportFormInput
          labelName='name'
          labelDisplayName='Nazwa'
          type='input'
          width='long'
        />
        <ReportFormInput
          labelName='description'
          labelDisplayName='Opis'
          type='textarea'
          width='long'
        />
        <ReportFormInput
          labelName='mainColor'
          labelDisplayName='Dominujący kolor'
          type='input'
          width='short'
        />
        <ReportFormInput
          labelName='foundPlace'
          labelDisplayName='Miejsce znalezienia'
          type='input'
          width='long'
        />
        <ReportFormInput
          labelName='foundDate'
          labelDisplayName='Data znalezienia'
          type='date'
          width='long'
        />
      </div>
      <button className='bg-custom-red mt-4 cursor-pointer rounded px-6 py-2 font-bold text-white'>
        ZATWIERDŹ
      </button>
    </section>
  );
};

export default ReportForm;
