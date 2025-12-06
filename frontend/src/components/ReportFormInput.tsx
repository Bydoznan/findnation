type Props = {
  labelName: string;
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
  return (
    <div className={`flex ${width === 'long' ? 'w-150' : 'w-75'} flex-col`}>
      <label
        htmlFor={labelName}
        className='mb-1 ml-2 text-neutral-500'>
        {labelDisplayName}
      </label>
      {type === 'input' ? (
        <input
          type='text'
          id={labelName}
          className='h-12 rounded-md border-2 border-black px-2'
        />
      ) : type === 'textarea' ? (
        <textarea
          maxLength={400}
          className='h-34 w-150 resize-none rounded-md border-2 border-black p-2'></textarea>
      ) : (
        <input
          type='date'
          id='date'
          className='h-12 rounded-md border-2 border-black px-2'
        />
      )}
    </div>
  );
};

export default ReportFormInput;
