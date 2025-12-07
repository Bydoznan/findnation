'use client';

import ReportFormInput, {
  Props as FormInputProps,
} from '@/components/ReportFormInput';
import { FormProvider, useForm } from 'react-hook-form';

export type FormData = {
  name: string;
  description: string;
  mainColor: string;
  foundPlace: string;
  foundDate: string;
};

const inputs: FormInputProps[] = [
  {
    labelName: 'name',
    labelDisplayName: 'Nazwa',
    type: 'input',
    width: 'long',
  },
  {
    labelName: 'description',
    labelDisplayName: 'Opis',
    type: 'textarea',
    width: 'long',
  },
  {
    labelName: 'mainColor',
    labelDisplayName: 'Dominujący kolor',
    type: 'input',
    width: 'long',
  },
  {
    labelName: 'foundPlace',
    labelDisplayName: 'Miejsce znalezienia',
    type: 'input',
    width: 'long',
  },
  {
    labelName: 'foundDate',
    labelDisplayName: 'Data znalezienia',
    type: 'date',
    width: 'long',
  },
];

const ReportForm = () => {
  const methods = useForm<FormData>();

  const { handleSubmit } = methods;

  const onSubmit = (data: FormData) => console.log(data);

  return (
    <FormProvider {...methods}>
      <form
        onSubmit={handleSubmit(onSubmit)}
        className='mt-32 mb-8 flex w-200 flex-col items-center justify-start bg-white p-10 shadow-xl'>
        <h1 className='font-inter my-8 text-2xl font-bold text-neutral-600'>
          FORMULARZ ZGŁOSZENIOWY
        </h1>
        <div className='flex flex-col items-start justify-center gap-4'>
          {inputs.map((inp) => (
            <ReportFormInput
              key={inp.labelName}
              labelName={inp.labelName}
              labelDisplayName={inp.labelDisplayName}
              type={inp.type}
              width={inp.width}
            />
          ))}
        </div>
        <button
          type='submit'
          className='bg-custom-red mt-16 cursor-pointer rounded px-6 py-2 font-bold text-white'>
          ZATWIERDŹ
        </button>
      </form>
    </FormProvider>
  );
};

export default ReportForm;
