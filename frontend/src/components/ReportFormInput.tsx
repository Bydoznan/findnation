import { FormData } from '@/components/ReportForm';
import { useEffect, useRef, useState } from 'react';
import { useFormContext } from 'react-hook-form';

export type Props = {
  labelName: keyof FormData;
  labelDisplayName: string;
  type: 'input' | 'textarea' | 'date';
  width: 'short' | 'long';
};

const ReportFormInput = ({
  labelName,
  labelDisplayName,
  type,
  width,
}: Props) => {
  const {
    register,
    formState: { errors },
  } = useFormContext<FormData>();

  const [descLength, setDescLength] = useState<number>(0);

  return (
    <div className={`flex ${width === 'long' ? 'w-150' : 'w-75'} flex-col`}>
      <label
        htmlFor={labelName}
        className='font-inter mb-1 ml-2 text-neutral-600'>
        {labelName === 'description'
          ? `${labelDisplayName} (${descLength}/400)`
          : labelDisplayName}
      </label>
      {type === 'input' ? (
        <input
          type='text'
          id={labelName}
          className='h-12 rounded-md border-2 border-black px-2'
          {...register(labelName)}
        />
      ) : type === 'textarea' ? (
        <textarea
          maxLength={400}
          className='h-34 w-150 resize-none rounded-md border-2 border-black p-2'
          {...register(labelName)}
          onChange={(e) => setDescLength(e.target.value.length)}></textarea>
      ) : (
        <input
          type='date'
          id='date'
          className='h-12 rounded-md border-2 border-black px-2'
          {...register(labelName)}
        />
      )}
    </div>
  );
};

export default ReportFormInput;
